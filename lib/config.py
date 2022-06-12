from json import loads
from pathlib import Path
import configparser

paths = [
    Path().cwd() / Path('config.ini'),
    Path().cwd() / Path('config_interface.ini')
]

parser = configparser.ConfigParser()

def setVarName(section, key):
    s = section.replace('-', '_').upper()
    k = key.replace('-', '').upper()
    return f'{s}_{k}'

def formatData(section, key):
    vals = parser.get(section, key)
    return loads(vals) if section == 'repr-poker' else vals
        
for path in paths:
    parser.read(path, encoding='utf-8-sig')
    for section in parser.sections():
        keys = parser.options(section)
        globals().update(dict(zip(
            map(lambda key: setVarName(section, key), keys),
            map(lambda key: formatData(section, key), keys)
        )))
