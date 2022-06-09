# pubnub-poker

This is a simple poker interface that allows people to play on one table over pubnub. It only offers basic functionality.

## Setup 
First off, someone has to obtain means of communication through [PubNub](https://www.pubnub.com/) by createing a (free) account and acquiring the **subscribe key** and **publish key** of a newly created project. Those keys have to be shared to every participating player.

### Environment setup
Every participant aiming to play should do the following steps
- clone this repo as `git clone https://github.com/kuco23/pubnub-poker.git --recurse-submodules`,
- install dependencies ([`pubnub`](https://pypi.org/project/pubnub/) and [`cryptography`](https://pypi.org/project/cryptography/)),
- rename `config_template.ini` to `config.ini` and fill in the relevant data (`uuid` is a unique user name).

One special (trusted) participant should run `dealer.py`, while everyone else should run `input.py` and `output.py` in seperate shells  (`git bash` sometimes hides python's printed output, so maybe use something else (`git bash` from vsc is ok)). 

### Game rules
Anything typed into the terminal running `input.py` should be visible to all from the terminal running `output.py`. Before beginning a game, everyone should send their public keys (cryptography thing that allows privately sending cards to the same channel) by sending (inputting) `send public key`. Then everyone should buyin by sending `buyin` (this will give a person 100$). From then on
- `STARTROUND` : start a new round
- `CALL` : call
- `CHECK` : check
- `FOLD` : fold
- `RAISE X` : raise amount `X`
- `ALLIN` : go all in

Everything written to the chat is visible to all (the dealer ignores what's not recognized as a command).

## TODO
- [ ] enable players leaving the table (without having to lose all money)
- [ ] enable money info queries


