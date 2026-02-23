# HTTP-Chunk-Streamer

A robust, lightweight video streaming engine built in Python that simulates the core behavior of Content Delivery Networks (CDNs). Ideally suited for understanding application-layer protocols, buffering strategies, and inter-process communication.

## Overview

This project implements a custom video streaming client that parses manifest files, fetches video chunks via HTTP, and pipes the data directly to a media player. It bypasses standard high-level libraries to handle the raw byte stream manually, ensuring efficient buffer management and smooth playback.

**Key Concepts:** `HTTP Range Requests`, `Producer-Consumer Pattern`, `TCP Sockets`, `Multithreading`, `Manifest Parsing`.

## Architecture

The system follows a multithreaded **Producer-Consumer** architecture to decouple network latency from video playback:

```mermaid
graph LR
    Server[Web Server] -- "HTTP GET (Range)" --> Producer[Producer Thread]
    Producer -- Chunks --> Buffer[("Queue / Buffer")]
    Buffer -- Chunks --> Consumer[Consumer Thread]
    Consumer -- TCP Socket --> Player["Media Player (VLC/MPlayer)"]
