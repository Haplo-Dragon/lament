import json
import character

char = character.LotFPCharacter()
print(json.dumps(char.__dict__))

with open('mocked_character.json', 'w') as f:
    json.dump(char.__dict__, f)
