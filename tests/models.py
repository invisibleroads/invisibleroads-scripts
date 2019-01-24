META_SEPARATOR = '# '


class Goal(object):

    _next_id = 0

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.text = kwargs['text']

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.text == other.text,
        ])

    @classmethod
    def _get_next_id(Class):
        id = Class._next_id
        Class._next_id += 1
        return id

    @classmethod
    def parse_text(Class, text):
        goal_text, _, meta_text = text.partition(META_SEPARATOR)
        goal_text = goal_text.strip()
        return Class(id=Class._get_next_id(), text=goal_text)

    def format_text(self):
        return '%s  %s%s' % (
            self.text,
            META_SEPARATOR,
            self._format_meta_text())

    def _format_meta_text(self):
        terms = []
        terms.append(self.id)
        return ' '.join(terms)
