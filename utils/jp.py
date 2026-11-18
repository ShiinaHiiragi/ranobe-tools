import re
import math
import unicodedata
from dataclasses import dataclass, replace
from html.parser import HTMLParser

kana_pattern = re.compile('[ぁ-ゖゝ-ゟァ-ヺヽ-ヿㇰ-ㇿ]')
han_pattern = re.compile('[㐀-䶿一-鿿𠀀-\U0002fa1f]')
kana_scale = 8.0
long_han = 6

class VisibleText(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.main, self.ruby, self.images = ([], [], [])
        self.rt = self.hidden = 0
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head'):
            self.hidden += 1
        if tag in ('rt', 'rp'):
            self.rt += 1
        if tag == 'img':
            attrs = dict(attrs)
            if attrs.get('src'):
                self.images.append(attrs['src'])

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('rt', 'rp'):
            self.rt = max(0, self.rt - 1)

    def handle_data(self, text):
        if not self.hidden:
            (self.ruby if self.rt else self.main).append(text)

@dataclass(frozen=True)
class OriginEvidence:
    text: str
    reading: str
    images: tuple
    kana: int
    han: int
    score: float
    active: bool

def parse_origin(source):
    visible = VisibleText(source)
    text = unicodedata.normalize('NFKC', ''.join(visible.main))
    reading = unicodedata.normalize('NFKC', ''.join(visible.ruby))
    kana_count, han_count = (len(kana_pattern.findall(text)), len(han_pattern.findall(text)))
    active = bool(kana_count or han_count or kana_pattern.search(reading))
    if not active:
        score = -20.0
    elif kana_count:
        score = kana_scale * kana_count / (kana_count + han_count)
    elif kana_pattern.search(reading):
        score = kana_scale
    else:
        score = -4.0 if han_count >= long_han else -0.1
    return OriginEvidence(
        text, reading, tuple(visible.images), kana_count, han_count, score, active
    )

def decode_origin(items, switch):
    if not items:
        return []
    change, stay = (math.log(switch), math.log(1 - switch))
    prev = [0.0, 0.0]
    back = []
    for item in items:
        current, parents = ([], [])
        for state in (0, 1):
            candidates = [
                prev[previous_state] + (stay if previous_state == state else change)
                for previous_state in (0, 1)
            ]
            parent = max(range(2), key=lambda previous_state: candidates[previous_state])
            current.append(candidates[parent] + (item.score if state else 0.0))
            parents.append(parent)
        back.append(parents)
        prev = current
    state = int(prev[1] > prev[0])
    result = []
    for parents in reversed(back):
        result.append(bool(state))
        state = parents[state]
    return result[::-1]

class RubyBase(VisibleText):
    def __init__(self, source):
        self.depth, self.base = (0, [])
        super().__init__(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'ruby':
            self.depth += 1
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag == 'ruby':
            self.depth = max(0, self.depth - 1)

    def handle_data(self, text):
        if self.depth and (not self.rt) and (not self.hidden):
            self.base.append(text)
        super().handle_data(text)

@dataclass(frozen=True)
class OriginDecision:
    role: str
    score: float | None

    @property
    def fade(self):
        return self.role == 'S'

def score_origin(item, source):
    kana_count, han_count = (item.kana, item.han)
    if not kana_count:
        if kana_pattern.search(item.reading):
            base = unicodedata.normalize('NFKC', ''.join(RubyBase(source).base))
            kana_count = 0.5 * min(
                len(han_pattern.findall(base)),
                len(kana_pattern.findall(item.reading))
            )
    if not kana_count:
        return -1.0 if han_count >= 6 else -0.1 if han_count else 0.0
    other = sum((character.isalnum() for character in item.text)) - item.kana - han_count
    return 8 * kana_count / max(1, kana_count + han_count + other) - 1.0

def origin_anchor(item):
    if item.score >= 3:
        return True
    if item.score <= -1 and item.han >= 6:
        return False
    return None

def count_origin(items):
    anchors = [origin_anchor(item) for item in items]
    pairs = [
        (previous_anchor, next_anchor) for previous_anchor, next_anchor in zip(anchors, anchors[1:])
        if previous_anchor is not None and next_anchor is not None
    ]
    return (
        sum((previous_anchor != next_anchor for previous_anchor, next_anchor in pairs)),
        len(pairs)
    )

def analyze_origin(pages):
    observations = [[parse_origin(item) for item in page] for page in pages]
    sequences, indices = ([], [])
    for source_page, page in zip(pages, observations):
        paragraph_indices = [index for index, item in enumerate(page) if item.text.strip()]
        sequence = [
            replace(page[index], score=score_origin(page[index], source_page[index]))
            for index in paragraph_indices
        ]
        alnum = [any((character.isalnum() for character in item.text)) for item in sequence]
        quoted = [
            any((unicodedata.category(character) in ('Ps', 'Pi') for character in item.text))\
                and any((
                    unicodedata.category(character) in ('Pe', 'Pf')
                    for character in item.text
                ))
            for item in sequence
        ]
        keep = [
            has_alnum or quoted[index]
            or (index > 0 and (not alnum[index - 1]))
            or (index + 1 < len(sequence) and (not alnum[index + 1]))
            for index, has_alnum in enumerate(alnum)
        ]
        indices.append([index for index, included in zip(paragraph_indices, keep) if included])
        sequence = [item for item, included in zip(sequence, keep) if included]
        normalized = [re.sub('\\s+', '', item.text) for item in sequence]
        copies = [
            index > 0\
                and normalized[index] == normalized[index - 1]\
                or (index + 1 < len(sequence) and normalized[index] == normalized[index + 1])
            for index in range(len(sequence))
        ]
        anchors = [
            origin_anchor(item)
            for item, copied in zip(sequence, copies)
            if not copied
        ]
        if anchors.count(True) >= 2 and anchors.count(False) >= 2:
            sequence = [
                replace(item, score=0.0) if copied else item
                for item, copied in zip(sequence, copies)
            ]
        sequences.append(sequence)
    counts = [count_origin(sequence) for sequence in sequences]
    total = sum((pair_count for _, pair_count in counts))
    prior = (sum((switch_count for switch_count, _ in counts)) + 1) / (total + 2)
    weight = min(64.0, total)
    cap = 1 / (1 + math.exp(-1.25))
    output = []
    for page, sequence, paragraph_indices, (changes, pair_count) in zip(
        observations, sequences, indices, counts
    ):
        switch = (changes + weight * prior + 1) / (pair_count + weight + 2)
        anchors = [anchor for item in sequence if (anchor := origin_anchor(item)) is not None]
        if len(anchors) >= 2 and (all(anchors) or not any((
            item.kana or kana_pattern.search(item.reading) for item in sequence
        ))):
            switch = 0.05
        switch = min(cap, max(1 - cap, switch))
        labels = decode_origin(sequence, switch)
        result = [OriginDecision('U', None) for _ in page]
        for index, item, label in zip(paragraph_indices, sequence, labels):
            result[index] = OriginDecision('S' if label else 'T', item.score)
        output.append(result)
    return output

def is_origin(line, decision=None):
    if decision is None:
        decision = analyze_origin([[line]])[0][0]
    return decision.fade
