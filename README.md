## Authors
- *Gonçalo Barros* - [github.com/barrosgoncalo](https://github.com/barrosgoncalo)
- *João Horta* - [github.com/jnhorta1](https://github.com/jnhorta1)

## Network Loss Simulation (Stress Testing)
To demonstrate the protocol's reliability, both the sender and receiver include a built-in **Network Loss Simulator**. 

- **Mechanism:** A randomizer determines whether each packet (data or ACK) is transmitted or "dropped" in the network.
- **Purpose:** This forces the **Go-Back-N** logic to trigger timeouts and retransmissions, proving that the file integrity is maintained even in unstable network conditions.
- **Verification:** The system guarantees a **Zero Loss / 100% Binary Match** between the source and destination files after the transfer.