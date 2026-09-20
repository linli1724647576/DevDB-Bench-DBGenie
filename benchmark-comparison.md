# Appendix: Comparison of DevDB-Bench with Existing Benchmarks

This appendix compares **DevDB-Bench** with representative database-oriented and software-development benchmarks across dataset scale, data sources, development settings, target outputs, database-design scope, and schema complexity. It supplements the benchmark statistics reported in the paper.

**Category legend:** 🟦 Database-oriented benchmarks · 🟧 Software-development benchmarks · 🟩 DevDB-Bench (ours)

## 1. Tasks, Sources, and Outputs

Table 1 summarizes the tasks addressed by each benchmark. Scale is reported in the original unit of each benchmark; questions, issues, tasks, projects, and programs are not interchangeable measures of difficulty or coverage.

**Table 1. Task-level comparison.**

| Benchmark | Scale | Source | Development setting | Target output |
| --- | --- | --- | --- | --- |
| 🟦 Spider [1] | 10,181 questions | Human-created NL–SQL pairs | Querying existing databases | `SELECT` query |
| 🟦 BIRD [2] | 12,751 questions | Human-created NL–SQL pairs | Querying existing databases | `SELECT` query |
| 🟦 Spider 2.0 [3] | 632 tasks | Enterprise data environments | Enterprise SQL workflows | SQL workflow |
| 🟦 RSchema [4] | 381 tasks | Synthesized scenarios and Web materials | Requirement-to-schema generation | Logical schema |
| 🟧 SWE-bench [5] | 2,294 issues | Real GitHub issues and repositories | Repository issue resolution | Code patch |
| 🟧 SWE-Dev [6] | 14K training / 500 test instances | Real repositories and feature changes | Repository feature development | Feature implementation |
| 🟧 E2EDev [7] | 46 projects | Real open-source Web applications | Requirement-to-Web-app generation | Executable Web application |
| 🟧 ProgramBench [8] | 200 programs | Real executables and documentation | Program reconstruction | Codebase and build script |
| 🟩 **DevDB-Bench** | **51 projects** | **Real application repositories** | **Application database design** | **DBMS-specific executable DDL** |

### 🟦 Database-oriented benchmarks

Spider, BIRD, and Spider 2.0 primarily evaluate queries or SQL workflows over existing databases. Their tasks assume that the database structures are already available and therefore do not directly assess the ability to derive a database design from application requirements.

RSchema, introduced by Text2Schema, moves beyond this setting by making the logical schema itself the generation target. Its instances are constructed from mixed sources, including synthesized scenarios and Web-based database-design materials such as tutorials and examples. It focuses on requirement-to-logical-schema generation, whereas DevDB-Bench is grounded in application repositories and targets database designs for application development.

### 🟧 Software-development benchmarks

SWE-bench and SWE-Dev evaluate issue resolution and feature implementation within existing repositories. E2EDev and ProgramBench evaluate project-level generation or reconstruction: E2EDev targets runnable Web applications from requirements, while ProgramBench targets programs reconstructed from reference executables and usage documentation. These benchmarks assess broader software-development capabilities but do not isolate database-design quality as an independent evaluation target. E2EDev excludes database-dependent setup to simplify execution.

## 2. Database-Design Coverage

Table 2 distinguishes four dimensions of application-level database design:

- **AP — Access patterns:** explicit descriptions of representative application operations used to guide database design.
- **LD — Logical design:** generation of tables, columns, relationships, and integrity constraints.
- **PD — Physical design:** generation of indexes informed by application access patterns.
- **Dialect DDL:** generation of executable data-definition statements for a specified DBMS dialect.

**Table 2. Database-design scope and coverage.**

| Benchmark | Database-design scope | AP | LD | PD | Dialect DDL |
| --- | --- | :---: | :---: | :---: | :---: |
| 🟦 Spider [1] | Existing database assumed | — | — | — | — |
| 🟦 BIRD [2] | Existing database assumed | — | — | — | — |
| 🟦 Spider 2.0 [3] | Existing database assumed | — | — | — | — |
| 🟦 RSchema [4] | Logical design only | — | ✓ | — | — |
| 🟧 SWE-bench [5] | Database design not specifically evaluated | — | — | — | — |
| 🟧 SWE-Dev [6] | Database design not specifically evaluated | — | — | — | — |
| 🟧 E2EDev [7] | Database-dependent setup excluded | — | — | — | — |
| 🟧 ProgramBench [8] | Database design not separately evaluated | — | — | — | — |
| 🟩 **DevDB-Bench** | **Database design as a first-class target** | **✓** | **✓** | **✓** | **✓** |

**Reading the table.** A check mark indicates that the dimension is explicitly included in the benchmark's database-design task. A dash indicates that it is not an explicit database-design target; it does not imply that every task excludes database-related code or SQL. In particular, generating queries in a SQL dialect is distinct from generating dialect-specific DDL for a new database design.

DevDB-Bench requires systems to jointly produce a requirement-faithful logical schema, access-pattern-aware indexes, and DDL executable under the specified DBMS. Its reference designs are reconstructed from application DDL files, migrations, and ORM models. Requirements and access-pattern descriptions are derived from application documentation and code, connecting the design task to application semantics and data usage.

## 3. Schema Complexity and Coverage

RSchema is the closest benchmark in terms of its generation target. Table 3 compares the average size of its logical schemas with the reference database designs in DevDB-Bench.

**Table 3. Average schema size.**

| Benchmark | Tables per instance | Columns per instance |
| --- | ---: | ---: |
| 🟦 RSchema [4] | 4.59 | 21.90 |
| 🟩 **DevDB-Bench** | **21.10** | **171.35** |

DevDB-Bench contains substantially larger schemas on average. These counts describe structural scale rather than establishing task difficulty on their own. Together with the source and scope comparisons, they characterize the benchmark's emphasis on database structures drawn from real applications.

The 51 DevDB-Bench instances span **13 application domains** and **six DBMS dialects**: PostgreSQL, MySQL, SQLite, SQL Server, MariaDB, and DuckDB. Reference designs contain an average of **23.27 foreign keys** and **19.25 indexes**, and the largest design contains **122 tables**. This coverage complements the table and column statistics by capturing relationships, physical-design structures, and dialect diversity.

## 4. Positioning of DevDB-Bench

DevDB-Bench connects database-design generation with end-to-end software development. Relative to Text-to-SQL benchmarks, it evaluates the creation of database structures rather than queries over existing structures. Relative to RSchema, it adds explicit application access patterns, physical design, and dialect-specific executable DDL. Relative to software-development benchmarks, it makes database design an independent evaluation target. The resulting task jointly examines application semantics, relational structure, access-pattern support, and executability.

## References

1. Tao Yu et al. 2018. *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task.* EMNLP. Paper citation key: `yu2018spider`.
2. Jinyang Li et al. 2023. *Can LLM Already Serve as a Database Interface? A BIG Bench for Large-Scale Database Grounded Text-to-SQLs.* NeurIPS. Paper citation key: `li2023can_dup1`.
3. Fangyu Lei et al. 2024. *Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows.* arXiv:2411.07763. Paper citation key: `lei2024spider_dup1`.
4. Qin Wang et al. 2025. *Text2Schema: Filling the Gap in Designing Database Table Structures Based on Natural Language.* arXiv:2503.23886. Paper citation key: `wang2025text2schema`.
5. Carlos E. Jimenez et al. 2024. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR. Paper citation key: `jimenez2023swebench`.
6. Yaxin Du et al. 2025. *SWE-Dev: Evaluating and Training Autonomous Feature-Driven Software Development.* arXiv:2505.16975. Paper citation key: `du2025swe`.
7. Jingyao Liu et al. 2026. *E2EDev: Benchmarking Large Language Models in End-to-End Software Development Task.* ACL. Paper citation key: `liu2026e2edev`.
8. John Yang et al. 2026. *ProgramBench: Can Language Models Rebuild Programs From Scratch?* arXiv:2605.03546. Paper citation key: `yang2026programbench`.
