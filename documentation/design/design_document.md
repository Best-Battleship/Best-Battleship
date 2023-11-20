# Design Document for Best Battleship

## Team members

- Oleg Tervo-Ridor
- Toni Raeluoto
- Jonne Kanerva
- Guanghan Wu

## Project description

The topic of the group project is a [Battleship game](<https://en.wikipedia.org/wiki/Battleship_(game)>) for any number of players. The players are arranged into a virtual ring where they always have do attack the next player in the ring. A token is used to specify the current player and is also used as the main mechanism for synchronization, consistency and consensus. The game will use the standard rules described in the Wikipedia article linked at the start of this paragraph.

### Technologies

The program for the game will be implemented in Python. Communication between nodes will happen via sockets. The messages will be JSON payloads. User Interface will be a Command-line Interface.

### Nodes and their roles

All nodes will be identical. Each node will have the option to either try to initialize a new game with the other nodes or to wait for some other node to initialize the game. The initializing node will always have the first turn in the game, but that is the only differentiating factor between the nodes regarding any of the gameplay or the communication logic.

### Messages

The semantics of the messages are described in the [communication protocols](#).

The messages sent between the programs will be JSON payloads of the following format:

```
{message: "EVENT_NAME" [, data: {}]}
```

where `"EVENT_NAME"` will adhere to some command defined in the [communication protocols](#) and `data` is an object holding data relevant to the specific command. The token used for synchronization, consistency and consensus will be added to the `data` object when necessary.

## Distribution and properties

The game has its state distributed among the participating players and the main mechanism for synchronization, consistency and consensus is a token that grants the right to play a turn and send messages that mutate the state of other players.

Participating players are distributed into a virtual ring, with the token being passed to the next player
after playing a turn. When playing a turn, all participating players validate that the correct token was used. If a token is lost due to any reason (e.g. a player holding the token failing), a new one will be generated to provide fault tolerance to the system.

### Game loop (simplified)

The described (simplified) game loop shows our intuition considering how to use the token to guarantee synchronization, consistency and consensus by only allowing the token holder to send commands that mutate the shared state.

For more robust descriptions, see the [communication protocol sequence diagrams](#).

1. Token holder does their move to the next player in the virtual ring
2. Others validate
3. Token holder passes token to the next player
4. Others validate
5. New token holder checks their board for a lose condition
6. Others validate
7. Move to step 1

### Summary for properties of the distributed system

- **Shared distributed state**:
  - players, which is a list of tuples (id, ip, port, game board)
    - The order of the list is also the order of the ring
    - id is used to identify individual players in commands
    - ip and port are used to send messages via sockets
    - game board is used:
      - to attack by the token holder
      - to validate attacks by others
- **Synchronization and consistency** provided by requiring all players to acknowledge a command sent by the token holder
- **Consensus** provided by the property that only the token holder is allowed to make mutations to the shared distributed state
- **Fault tolerance** provided by remaining players generating a new token if player holding the token fails

\pagebreak

## Appendix A Communication sequence diagrams

### Game initialization

```mermaid
sequenceDiagram
    participant Initiator as initiator
    participant Node1 as node
    participant Node2 as node
    participant other as other


    Initiator->>Node1: INIT_GAME
    Initiator->>Node2: INIT_GAME
    Initiator->>other: INIT_GAME

    Node1->>Initiator: JOIN_GAME
    Initiator-->>Node1: ACK_JOIN(id)
    Node2->>Initiator: JOIN_GAME
    Initiator-->>Node2: ACK_JOIN(id)
    Note over Initiator,Node2: Waiting constant time

    Initiator->>Node1: START_GAME[id-IP list]
    Node1-->>Initiator: ACK
    Initiator->>Node2: START_GAME[id-IP list]
    Node2-->>Initiator: ACK
```

### Game Cycle

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PLAY_TURN (Move, Token)
    Node1-->>Initiator: PLAY_TURN (Move)
    Initiator->>Node2: PLAY_TURN (Move, Token)
    Node2-->>Initiator: PLAY_TURN (Move)

    Initiator->>Node1: PASS_TOKEN (Token, 1)
    Node1-->>Initiator: PASS_TOKEN (1)
    Initiator->>Node2: PASS_TOKEN (Token, 1)
    Node2-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node1: PASS_TOKEN_CONFIRMED
    Node1->>Initiator: MOVE_RESULT (Result, Token)
    Initiator-->>Node1: MOVE_RESULT (Result)

    Node1->>Node2: MOVE_RESULT (Result, Token)
    Node2-->>Node1: MOVE_RESULT (Result)
    Node1-->>Initiator: PLAY_TURN (Move,Token)
    Initiator-->>Node1: PLAY_TURN (Move)

    Node1->>Node2: PLAY_TURN (Move,Token)
    Node2-->>Node1: PLAY_TURN (Move)

```

### Node timeout

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PLAY_TURN (Move, Token)
    Node1-->>Initiator: PLAY_TURN (Move)
    Initiator->>Node2: PLAY_TURN (Move, Token)
    Note over Initiator,Node2: Node with a token waits constant time

    Initiator->>Node1: TIMEOUT (Id, Token)
    Node1-->>Initiator: TIMEOUT (Id)
    Initiator->>Node2: TIMEOUT (Id, Token)
    Note over Initiator,Node2: Node with a token waits constant time, offline node can still answer NAK


    Initiator->>Node1: DROP (Id, Token)
    Node1-->>Initiator: DROP (Id)
    Initiator->>Node2: DROP (Id, Token)
    Note over Initiator,Node2: Continue the game, here for example node 0 pass the token next, ignore all messages from the node 2

```

### Node timeout recovery

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PLAY_TURN (Move, Token)
    Node1-->>Initiator: PLAY_TURN (Move)
    Initiator->>Node2: PLAY_TURN (Move, Token)
    Note over Initiator,Node2: Node with a token waits constant time

    Initiator->>Node1: TIMEOUT (Id, Token)
    Node1-->>Initiator: TIMEOUT (Id)
    Initiator->>Node2: TIMEOUT (Id, Token)
    Node2-->>Initiator: NAK

    Initiator->>Node1: PLAY_TURN (Move, Token, RepeatedFlag)
    Node1-->>Initiator: PLAY_TURN (Move,Flag)

    Initiator->>Node2: PLAY_TURN (Move, Token, RepeatedFlag)
    Node2-->>Initiator: PLAY_TURN (Move,Flag)
    Note over Initiator,Node2: Continue the game as usual


```

### Token lost in game

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PASS_TOKEN (1, Token)
    Node1-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node2: PASS_TOKEN (1, Token)
    Node2-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node1: PASS_TOKEN_CONFIRMED
    Note over Initiator,Node2: Node 1 goes offline, everyone has a timer set on (conterclockwise distance from token * const)s, node 0 timer ends.

    Initiator->>Node1: ELECTION
    Initiator->>Node2: ELECTION
    Node2-->>Initiator: ACK_ELECTION
    Note over Initiator,Node2: Node 0 waits for constant time, this is the last chance for node 1 to answer NAK

    Initiator->>Node1: DROP (1, NewToken)
    Initiator->>Node2: DROP (1, NewToken)
    Node2-->>Initiator: DROP(1)
    Initiator->>Node2: PASS_TOKEN (NextPlayerId, NewToken)
    Node2-->>Initiator: PASS_TOKEN (NextPlayerId)
    Initiator->>Node2: PASS_TOKEN_CONFIRMED
    Note over Initiator,Node2: The game continues, other node 1 messages are ignored

```

### Token recovered

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PASS_TOKEN (1, Token)
    Node1-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node2: PASS_TOKEN (1, Token)
    Node2-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node1: PASS_TOKEN_CONFIRMED
    Note over Initiator,Node2: Node 1 struggles to make a move, node 0 timer ends

    Initiator->>Node1: ELECTION
    Node1-->>Initiator: NAK(Token)
    Initiator->>Node2: ELECTION
    Node2-->>Initiator: ACK_ELECTION
    Note over Initiator,Node2: Waiting for node 0 timer ends again, repeat constant times, then DROP and start ELECTION
    Note over Initiator,Node2: If nodes with token make a turn, continue game

    Node1->>Initiator: PLAY_TURN (Move, Token)
    Initiator-->>Node1: PLAY_TURN (Move)
    Node1->>Node2: PLAY_TURN (Move, Token)
    Node2-->>Node1: PLAY_TURN (Move)

    Note over Initiator,Node2: ...
```

### Player lost or left the game

```mermaid
sequenceDiagram
    participant Initiator as initiator (node 0)
    participant Node1 as node 1
    participant Node2 as node 2

    Initiator->>Node1: PLAY_TURN (Move, Token)
    Node1-->>Initiator: PLAY_TURN (Move)
    Initiator->>Node2: PLAY_TURN (Move, Token)
    Node2-->>Initiator: PLAY_TURN (Move)

    Initiator->>Node1: PASS_TOKEN (1, Token)
    Node1-->>Initiator: PASS_TOKEN (1)
    Initiator->>Node2: PASS_TOKEN (1, Token)
    Node2-->>Initiator: PASS_TOKEN (1)

    Initiator->>Node1: PASS_TOKEN_CONFIRMED
    Node1->>Initiator: MOVE_RESULT (Result, Token)
    Initiator-->>Node1: MOVE_RESULT (Result)

    Node1->>Node2: MOVE_RESULT (Result, Token)
    Node2-->>Node1: MOVE_RESULT (Result)
    Node1->>Initiator: LOST (1,Token)
    Initiator-->>Node1: LOST (1)

    Node1->>Node2: LOST (1,Token)
    Node2-->>Node1: LOST (1)

    Node1->>Initiator: PASS_TOKEN (2,Token)
    Initiator-->>Node1: PASS_TOKEN (2)

    Node1->>Node2: PASS_TOKEN (2,Token)
    Node2-->>Node1: PASS_TOKEN (2)
    Node1->>Node2: PASS_TOKEN_CONFIRMED
```
