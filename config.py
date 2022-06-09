from pathlib import Path
import configparser

path = Path().cwd() / Path('config.ini')

parser = configparser.ConfigParser()
parser.read(path, encoding='utf-8-sig')

def setVarName(section, key):
    s = section.replace('-', '_').upper()
    k = key.replace('-', '').upper()
    return f'{s}_{k}'

for section in parser.sections():
    keys = parser.options(section)
    globals().update(dict(zip(
        map(lambda key: setVarName(section, key), keys),
        map(lambda key: parser.get(section, key), keys)
    )))
