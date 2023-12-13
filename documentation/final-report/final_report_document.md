# Final Report for Best Battleship

\pagebreak

## Table of Contents

## Team members

- Oleg Tervo-Ridor
- Toni Raeluoto
- Jonne Kanerva 
- Guanghan Wu

## The project's goal and core functionality

**PROMPT:** *"The project’s goal(s) and core functionality. Identifying the applications / services that can build on your project."*

The topic of the group project is a [Battleship game](https://en.wikipedia.org/wiki/Battleship_(game)) for any number of players. The players are arranged into a virtual ring where they always have do attack the next player in the ring. A token is used to specify the current player and is also used as the main mechanism for synchronization, consistency and consensus. The game uses the standard rules described in the Wikipedia article linked at the start of this paragraph.

The game is built as a Python program that can be run on multiple nodes that then communicate via sockets. Node discovery is done by one of the nodes by broadcasting a INIT_GAME message, which is the replied to by nodes (JOIN_GAME) that want to join that particular game. After a certain amount of time, the initiating node starts the game (START_GAME) and sends the relevant data (token, tuples (id, ip, port)) to all the participating nodes. After that the nodes start playing the game by following the protocols described in the appendix. Token holder is always known and both the token and the move are validated by all nodes, which provides synchronization and consensus to the system.

The idea of having a virtual ring and a token could be used to implement any turn-based game that can be played in such a ring.

## Design Principles

**PROMPT:** *"The design principles (architecture, process, communication) techniques."*

The main design principle is that we wanted every node to be identical in terms of functionality, which lead us to a peer-to-peer architecture. Each node can initiate a game and each node can join a game. The initiating node serves a special purpose only when initiating the game, after which it is "demoted" to an identical state with all the participating nodes. All mutations require consensus, which is provided all nodes acknowledging that the node triggering a mutation (i.e. playing a turn in the battleship game) holds a valid token and is trying to play a valid turn. Passing the token to the next node also requires acknowledgement from all participants.

The nodes are arranged into a virtual ring, in which a token is rotated. The token holder is allowed to mutate the distributed state, which is in normal mode either playing a turn or letting others know what effect the previous player's turn had (HIT or MISS) so that the other nodes can record the event. All moves are always done against the next player in the ring, which provides an equal playing ground, preventing e.g. some participants agreeing on destroying a specific opponent first.

The nodes communicate via sockets. All communication is done with JSON messages, which contain the message (a string enum), possibly the token and relevant data for the message, such as the coordinates in case of a PLAY_TURN message.

**ELABORATE:** The nodes can be thought of as finite state machines that move mostly between states IDLE and PLAY_TURN.

### Messages

The semantics of the messages are described in the communication protocols provided as an appendix.

The messages sent between the programs will be JSON payloads of the following format:
```
{message: "EVENT_NAME" [, data: {}]}
```

where `"EVENT_NAME"` will adhere to some command defined in the communication protocols and `data` is an object holding data relevant to the specific command. The token used for synchronization, consistency and consensus will be added to the `data` object when necessary.

### Game loop (simplified)

The described (simplified) game loop shows our intuition considering how to use the token to guarantee synchronization, consistency and consensus by only allowing the token holder to send commands that mutate the shared state.

For more robust descriptions, see the communication protocol sequence diagrams provided as an appendix.

1. Token holder does their move to the next player in the virtual ring
2. Others validate
3. Token holder passes token to the next player
4. Others validate
5. New token holder checks their board for a lose condition
6. Others validate
7. Move to step 1

## Distribution and properties

**PROMPT**: *"What functionalities does your system provide? For instance, naming and node discovery,
consistency and synchronization, fault tolerance and recovery, etc? For instance, fault tolerance
and consensus when a node goes down."*

The game has its state distributed among the participating players and the main mechanism for synchronization, consistency and consensus is a token that grants the right to play a turn and send messages that mutate the state of other players.

Participating players are distributed into a virtual ring, with the token being passed to the next player
after playing a turn. When playing a turn, all participating players validate that the correct token was used. If a token is lost due to any reason (e.g. a player holding the token failing), a new one will be generated to provide fault tolerance to the system.

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

## Scaling

**PROMPT**: *"How do you show that your system can scale to support the increased number of nodes?"*

The application has no hard limits on the number of players as the ring can theoretically hold any number of players, but realistically the number of players is restricted to the subnet of the initializing node, as node discovery is done by broadcasting within the subnet.

## Performance

**PROMPT**: *"How do you quantify the performance of the system and what did you do (can do) to improve the performance of the system (for instance reduce the latency or improve the throughput)?"*

## The key enablers and the lessons learned during the development of the project.

**PROMPT**: *"The key enablers and the lessons learned during the development of the project."*

One key learning is that it is imperative to think on the architecture / interface lavel especially when working asynchronously as splitting the work can be difficult if the code organization does not support that.

It is also not trivial to come up with mechanisms that provide the desired properties in a distributed system like this, such as node discovery or consensus.

## Notes about the group member and their participation, work task division, etc.

**PROMPT**: *"Here you also may report, if you feel that the points collected to group should be split unevenly among group members. Use percentages when descripting this balancing view point."*

\pagebreak

## Appendix A Communication sequence diagrams

![Game initialization](../protocols/1-Start.jpg)

![Game cycle](../protocols/2-GameCycle.jpg)

![Node timeout](../protocols/3-Timeout.jpg)

![Node timeout recovery](../protocols/4-TimeoutNodeRecovered.jpg)

![Token lost in game](../protocols/5-TokenLost.jpg)

![Token recovered](../protocols/6-TokenNodeRecovered.jpg)

![Player lost or left the game](../protocols/7-PlayerLostOrSurrendered.jpg)
