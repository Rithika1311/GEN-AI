from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

pdf_path = Path(__file__).resolve().parent / "sample.pdf"

doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=letter,
    leftMargin=54,
    rightMargin=54,
    topMargin=54,
    bottomMargin=54,
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Title"],
    fontSize=22,
    leading=26,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=14,
)

h1_style = ParagraphStyle(
    "Heading1",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    textColor=colors.HexColor("#2563eb"),
    spaceBefore=12,
    spaceAfter=8,
)

h2_style = ParagraphStyle(
    "Heading2",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#334155"),
    spaceBefore=10,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontSize=10,
    leading=14.5,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=8,
)

story = []

# --- PAGE 1: Consensus Algorithms & Raft ---
story.append(Paragraph("Foundations of Modern Distributed Systems", title_style))
story.append(Paragraph("Chapter 1: Distributed Consensus and Leader Election in Raft", h1_style))
story.append(Paragraph(
    "Distributed consensus algorithms ensure that a collection of independent machines can maintain a consistent, "
    "replicated state machine even in the presence of unreliable network connections and node failures. "
    "Among contemporary protocols, the Raft consensus algorithm was intentionally designed for comprehensibility "
    "and formal verifiability while offering equivalent fault-tolerance guarantees to Paxos.",
    body_style
))
story.append(Paragraph("1.1 The Raft Leader Election Lifecycle", h2_style))
story.append(Paragraph(
    "In a Raft cluster, every node exists in one of three mutually exclusive states: Leader, Follower, or Candidate. "
    "During ordinary steady-state operation, the cluster contains exactly one Leader while all remaining nodes act as Followers. "
    "The Leader periodically broadcasts AppendEntries heartbeats across the network to assert its authority. "
    "If a Follower node fails to receive any heartbeat within an elapsed period termed the election timeout, it infers that "
    "the leader has crashed or become partitioned. The follower transitions to Candidate state, increments the monotonic term counter, "
    "votes for itself, and broadcasts RequestVote RPC requests in parallel to all peers in the cluster.",
    body_style
))
story.append(Paragraph("1.2 Randomized Timers and Split-Vote Mitigation", h2_style))
story.append(Paragraph(
    "A fundamental vulnerability in synchronous voting schemes is the split-vote dilemma, where multiple candidates commence elections "
    "simultaneously and divide the available ballots such that no candidate secures a strict majority. "
    "Raft prevents split-vote scenarios by employing randomized election timeouts typically chosen uniformly at random between 150ms and 300ms. "
    "This randomization staggers the timing of candidacy declarations, ensuring that in almost all cases a single candidate declares candidacy first, "
    "gathers the requisite majority of votes, and establishes leadership before competing candidates timeout.",
    body_style
))
story.append(Paragraph("1.3 Log Replication Mechanics", h2_style))
story.append(Paragraph(
    "Once established, all client mutations are directed exclusively to the cluster leader. The leader assigns a monotonically increasing "
    "log index and term number to the entry, appends the mutation to its local Write-Ahead Log (WAL), and propagates AppendEntries RPCs. "
    "A log entry is safely committed once it has been durably acknowledged by a quorum majority of nodes (floor(N/2) + 1). "
    "Once committed, the leader applies the entry to its local state machine and returns the execution result to the invoking client.",
    body_style
))

story.append(PageBreak())

# --- PAGE 2: Storage Engines & Indexing ---
story.append(Paragraph("Chapter 2: Storage Engine Architectures and LSM-Trees", h1_style))
story.append(Paragraph(
    "Database storage engines govern how records are organized on persistent secondary storage. "
    "The two dominant paradigms in modern data systems are B-Tree index structures and Log-Structured Merge (LSM) Trees. "
    "Each architecture represents distinct engineering trade-offs regarding read latency, write throughput, and storage overhead.",
    body_style
))
story.append(Paragraph("2.1 B-Trees vs. LSM-Trees: Mutation Dynamics", h2_style))
story.append(Paragraph(
    "Traditional relational databases employ B-trees and their variants (such as B+ trees), which arrange data into fixed-size pages "
    "(commonly 4KB to 16KB). When modifying a record, B-trees perform in-place random disk page overwrites. "
    "While this yields predictable point-lookup speeds of O(log N), it creates significant write amplification on rotational and solid-state disks "
    "due to random I/O bottlenecks. Conversely, LSM-trees convert all write operations into sequential disk writes. In an LSM-tree, mutations "
    "are initially buffered in an in-memory, sorted data structure called the MemTable (often backed by a Red-Black tree or SkipList), "
    "alongside an append-only Write-Ahead Log to guard against node crashes.",
    body_style
))
story.append(Paragraph("2.2 SSTables and the Role of Bloom Filters", h2_style))
story.append(Paragraph(
    "When an in-memory MemTable reaches its configured capacity threshold (typically 32MB to 64MB), it is frozen and flushed sequentially "
    "to persistent disk as an immutable Sorted String Table (SSTable). Because keys within an SSTable are strictly ordered, searches "
    "within a single SSTable can be completed in O(log K) steps. However, searching for a non-existent key across multiple disk SSTables "
    "can cause severe read amplification. To prevent superfluous disk page fetches, LSM engines pair each SSTable with a Bloom filter. "
    "A Bloom filter is a space-efficient probabilistic data structure that can deterministically assert whether a target key is definitely not present, "
    "completely eliminating expensive disk reads for absent keys.",
    body_style
))
story.append(Paragraph("2.3 Compaction Algorithms and Write Amplification", h2_style))
story.append(Paragraph(
    "As successive SSTables accumulate across disk tiers, background compaction worker routines continuously execute to maintain query performance. "
    "Compaction reads multiple overlapping SSTables, performs multi-way mergesort, removes overwritten versions and tombstoned deletions, "
    "and writes fresh, defragmented SSTables into higher tier levels. The repeated reading, merging, and rewriting of data induces write amplification, "
    "which is quantified as the ratio of bytes written to persistent media relative to logical bytes supplied by the client application.",
    body_style
))

story.append(PageBreak())

# --- PAGE 3: Distributed Transactions & Isolation ---
story.append(Paragraph("Chapter 3: Distributed Transactions and Isolation Levels", h1_style))
story.append(Paragraph(
    "Executing atomic, multi-partition transactions across independent physical servers introduces profound coordination complexity. "
    "Distributed transaction protocols must safeguard ACID guarantees despite physical network partitions, arbitrary clock drift, "
    "and asynchronous coordinator crashes.",
    body_style
))
story.append(Paragraph("3.1 The Two-Phase Commit Protocol (2PC)", h2_style))
story.append(Paragraph(
    "The fundamental coordination mechanism for distributed atomicity is the Two-Phase Commit (2PC) protocol. "
    "The protocol operates across two distinct stages: Phase 1 (The Prepare Phase) and Phase 2 (The Commit Phase). "
    "In Phase 1, the transaction coordinator sends a PREPARE message to every participant resource manager. Each participant acquires the necessary "
    "row locks, durably flushes redo/undo logs to stable storage, and replies with either a YES or NO ballot. "
    "In Phase 2, if all participants voted YES, the coordinator writes a COMMIT record to its log and issues COMMIT commands to all participants. "
    "If any participant replied NO or failed to respond within a timeout threshold, the coordinator broadcasts an ABORT directive. "
    "The primary drawback of 2PC is that it is a blocking protocol: if the coordinator crashes during Phase 2, participants remain blocked holding locks.",
    body_style
))
story.append(Paragraph("3.2 Time Synchronization and Spanner TrueTime", h2_style))
story.append(Paragraph(
    "Ordering transactions across globally distributed datacenters without global lock synchronization requires accurate timestamps. "
    "Standard physical clocks synchronizing over Network Time Protocol (NTP) experience non-deterministic clock skew of dozens or hundreds of milliseconds. "
    "Google Spanner mitigates clock skew using the TrueTime API, which directly exposes physical time uncertainty as an interval [earliest, latest] "
    "with a guaranteed bound epsilon (typically under 7ms). TrueTime nodes integrate atomic clocks and GPS receivers across datacenter master units. "
    "Spanner achieves external consistency (Strict Serializability) by introducing commit wait: the commit procedure deliberately pauses until "
    "the absolute real-time timestamp is guaranteed to have surpassed the transaction commit timestamp.",
    body_style
))
story.append(Paragraph("3.3 Strict Serializability vs. Snapshot Isolation", h2_style))
story.append(Paragraph(
    "Strict Serializability (also termed External Consistency) guarantees that the apparent execution order of all transactions corresponds "
    "to their actual real-time completion sequence without stale reads or concurrency anomalies. "
    "In contrast, Snapshot Isolation (SI) allows transactions to read from a consistent temporal snapshot taken at transaction initiation. "
    "While Snapshot Isolation eliminates dirty reads, non-repeatable reads, and phantom reads, it remains susceptible to write skew anomalies, "
    "where concurrent transactions evaluate mutually disjoint rows that overlap under business logic constraints.",
    body_style
))

story.append(PageBreak())

# --- PAGE 4: Caching & Replication Strategies ---
story.append(Paragraph("Chapter 4: Distributed Caching and Dynamo Replication", h1_style))
story.append(Paragraph(
    "Modern high-scale web platforms employ distributed in-memory caching layers (such as Redis and Memcached) "
    "alongside quorum-replicated distributed datastores to satisfy aggressive sub-millisecond Service Level Objectives (SLOs).",
    body_style
))
story.append(Paragraph("4.1 Caching Topologies: Write-Through vs. Write-Back", h2_style))
story.append(Paragraph(
    "Write-through caching updates both the in-memory cache and the backing relational database synchronously before acknowledging "
    "the write operation to the client. This guarantees strict data consistency between the cache and datastore, at the cost of higher write latency. "
    "Conversely, write-back (or write-behind) caching commits mutations immediately to the low-latency cache, asynchronously batching "
    "subsequent writes to the persistent datastore. While write-back yields tremendous write throughput, unpersisted cache contents are vulnerable "
    "to permanent loss if memory power is interrupted prior to downstream replication.",
    body_style
))
story.append(Paragraph("4.2 Cache Stampede and Mitigation Mechanisms", h2_style))
story.append(Paragraph(
    "A cache stampede (or thundering herd effect) occurs when a high-traffic, frequently requested cache key expires simultaneously under heavy load. "
    "Dozens or thousands of concurrent worker threads encounter a cache miss at the exact same instant and simultaneously bombard the underlying "
    "database with identical complex queries, saturating connection pools and inducing database failure. "
    "Systems defend against cache stampedes using distributed mutex locking (single-flight locking), background refresh cron loops, "
    "or probabilistic early recomputation (the XFetch algorithm), which recomputes the cached value shortly before official TTL expiration.",
    body_style
))
story.append(Paragraph("4.3 Quorum Replication: The R + W > N Invariant", h2_style))
story.append(Paragraph(
    "Leaderless distributed databases (such as Amazon Dynamo and Apache Cassandra) employ quorum consensus parameters defined by three integers: "
    "N (replication factor), R (read quorum size), and W (write quorum size). To guarantee strong consistency, the cluster must satisfy "
    "the mathematical invariant R + W > N. When this inequality holds, the set of nodes read and the set of nodes written are guaranteed to "
    "intersect on at least one replica node, allowing version vector reconciliation to identify and deliver the most recent write.",
    body_style
))
story.append(Paragraph("4.4 Sloppy Quorums and Hinted Handoff", h2_style))
story.append(Paragraph(
    "To maximize write availability during severe network partitions, Dynamo implementations support sloppy quorums. "
    "If the designated primary replica nodes for a key are unreachable, writes are temporarily accepted by healthy alternative nodes outside the primary "
    "preference list. These surrogate nodes store the payload alongside metadata known as a hinted handoff. Once network reachability to the primary "
    "replicas is restored, the surrogate nodes deliver the hinted records to complete replication.",
    body_style
))

story.append(PageBreak())

# --- PAGE 5: Network Protocols & Fault Tolerance ---
story.append(Paragraph("Chapter 5: Network Protocols, QUIC, and Fault Resilience", h1_style))
story.append(Paragraph(
    "Reliable distributed communication requires transport protocols and resilience patterns capable of isolating localized partial failures "
    "from triggering cascading cluster outages.",
    body_style
))
story.append(Paragraph("5.1 Overcoming TCP Head-of-Line Blocking with HTTP/3 QUIC", h2_style))
story.append(Paragraph(
    "In traditional HTTP/2 implementations over TCP, multiple independent request/response streams are multiplexed across a single TCP connection. "
    "However, because TCP treats the entire byte stream as a strictly ordered linear sequence, a single dropped packet causes TCP Head-of-Line (HoL) "
    "blocking: all concurrent multiplexed streams are forced to pause until the lost packet is retransmitted and acknowledged. "
    "HTTP/3 completely eliminates TCP head-of-line blocking by employing QUIC, an encrypted transport protocol built over UDP. "
    "QUIC implements packet loss recovery independently per stream, allowing unaffected streams to proceed without interruption.",
    body_style
))
story.append(Paragraph("5.2 The Circuit Breaker Pattern", h2_style))
story.append(Paragraph(
    "In microservices architectures, an unresponsive dependency can rapidly consume caller thread pools and exhaust system memory. "
    "The circuit breaker pattern wraps vulnerable remote procedure calls and monitors failure rates across a sliding time window. "
    "A standard circuit breaker operates across three finite states: "
    "1. Closed: Normal operation where incoming requests pass through to the target service. "
    "2. Open: When failure percentages surpass a threshold, the breaker trips to Open, instantly failing subsequent calls without attempting network I/O. "
    "3. Half-Open: After a predetermined reset timeout, the breaker enters Half-Open, permitting a limited number of trial requests through. "
    "If the trial requests succeed, the breaker resets to Closed; if failures persist, it reverts to Open.",
    body_style
))
story.append(Paragraph("5.3 Exponential Backoff with Jitter", h2_style))
story.append(Paragraph(
    "When client calls fail due to transient network blips or remote throttling, blindly retrying at fixed intervals exacerbates backend congestion. "
    "Exponential backoff progressively increases the wait time between retry attempts (e.g., t * 2^attempt). "
    "However, if an outage affects many clients simultaneously, standard exponential backoff causes all clients to retry in lockstep synchronized waves. "
    "Adding jitter introduces pseudo-random variance (such as Full Jitter: sleep = random_between(0, min(max_backoff, base * 2^attempt))) "
    "which disperses retries smoothly over time, breaking synchronous wave collisions and permitting the degraded service to recover.",
    body_style
))

doc.build(story)
print(f"Generated sample PDF at: {pdf_path} (File size: {pdf_path.stat().st_size} bytes)")
