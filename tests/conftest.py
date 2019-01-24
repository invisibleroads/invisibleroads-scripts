from os.path import dirname, join


FOLDER = dirname(__file__)
EXAMPLES_FOLDER = join(FOLDER, 'examples')


def load(file_name):
    return open(join(EXAMPLES_FOLDER, file_name)).read()


MISSION_TEXTS = [
    load('mission0.md'),
    load('mission1.md'),
    load('mission2.md'),
    load('mission3.md'),
    load('mission4.md'),
    load('missionX.md'),
]
