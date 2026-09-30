# Command-line application profile

Apply this profile to an affected component whose application types include `cli`. It supplements the base specification and design standards with command-line interaction questions.

## Specification questions

- How do command-line arguments, environment variables, configuration files, and defaults interact, and what is their precedence?
- What do stdin, stdout, and stderr contain on success, validation failure, and runtime failure? Is output intended for humans, scripts, or both?
- Which exit codes represent success, usage errors, partial results, and operational failures?
- What changes between TTY and non-TTY execution, including prompts, progress output, color, and pagination?
- What text encoding, newline, quoting, and binary-data behavior is guaranteed for input and output?

## Design and verification questions

- How are signals, cancellation, child-process termination, and cleanup handled, including interruption during output or mutation?
- Can output be piped without progress or diagnostic text corrupting the data stream?
- Are arguments and configuration errors actionable without exposing secrets?
- Verify representative TTY and non-TTY flows, stdin/pipeline behavior, exit codes, encoding, and signal/cancellation behavior where relevant.
