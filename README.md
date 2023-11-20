# Best-Battleship

CSM13001 Group Project

## Project description

The topic of the group project is a [Battleship game](<https://en.wikipedia.org/wiki/Battleship_(game)>) for any number of players.

### Technologies

Players will be Python programs that connect to each other via sockets.

## Distribution and properties

The game has its state distributed among the participating players and the main mechanism for coordination, consistency and consensus is a token that grants the right to play a turn.
Participating players are distributed into a virtual ring, with the token being passed to the next player
after playing a turn. When playing a turn, all participating players validate that the correct token was used. If a token is lost due to any reason (e.g. a player holding the token failing), a new one will be generated to provide fault tolerance to the system.

In a list format:

- **Shared distributed state** is the game board that is local to all participating players
- **Synchronization and consistency** provided by requiring all players to acknowledge a move
- **Consensus** provided by using a virtual ring and a token to grant right to move and move validation
- **Fault tolerance** provided by remaining players generating a new token if player holding the token fails

Messages:

- **Init_game**
- **Join_game**
  - response_ack(game participant id)
- **start_game**
  - player_ids
  - starting_playerID

## How to generate markdown file to PDF in Ubuntu

1. Install Ubuntu depencencies `sudo apt-get install pandoc texlive-latex-recommended texlive-latex-extra`

2. Install `mermaid-filter` for pandoc: `npm install mermaid-filter` (required by pandoc when rendering mermaid diagrams)

3. Generate document `cd documentation/design/ && pandoc design_document.md -s -o  ~/test.pdf`, make sure your current directory is the root of the project before the command.
