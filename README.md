Network Application: Torrent Tracker and Peer
Objective:
Build a Simple Torrent-like Application (STA) with the protocols defined by each group, using the TCP/IP protocol stack and must support multi-direction data transfering (MDDT).

APPLICATION DESCRIPTION:
The application includes the two types of hosts: tracker and node.

A centralized tracker keeps track of multiple nodes and stores what pieces of files.
Through tracker protocol, a node informs the server as to what files are contained in its local repository but does not actually transmit file data to the server.
When a node requires a file that does not belong to its repository, a request is sent to the tracker.
MDDT: The client can download multiple files from multiple source nodes at once, simultaneously.
This requires the node code to be a multithreaded implementation.

Features
Centralized Tracker:
Manages metadata and tracks nodes' file availability.
Uses an HTTP-based protocol for communication.
Multidirectional Data Transfer (MDDT):
Simultaneously download multiple file pieces from different peers.
Peer-to-Peer File Sharing:
Share files between nodes.
Start seeding downloaded files to other peers.
Metadata Management:
Magnet text and .torrent file handling.
Accurate mapping between file pieces and their addresses.
Statistics Dashboard:
Monitor upload/download progress in real-time.


