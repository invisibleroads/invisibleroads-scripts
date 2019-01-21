from os.path import dirname, join


FOLDER = dirname(__file__)
EXAMPLES_FOLDER = join(FOLDER, 'examples')
BLANK_MISSION_TEXT = open(join(EXAMPLES_FOLDER, 'blank.md')).read()
FULL_MISSION_TEXT = open(join(EXAMPLES_FOLDER, 'full.md')).read()
