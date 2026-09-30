# Mobile application profile

Apply this profile to an affected component whose application types include `mobile`. It supplements the base specification and design standards with mobile lifecycle and device questions.

## Specification questions

- What does the user observe when the app moves between foreground, background, suspension, and resume?
- Which state must survive navigation, process death, device restart, or restoration on another device?
- Which permissions are requested, when are they needed, and how does denial or later revocation affect behavior?
- What behavior is guaranteed offline and during network loss, reconnection, or captive-portal transitions?
- Which orientation, display sizes, accessibility settings, and assistive technologies are supported?
- Do signing, packaging, store metadata, or release-channel changes affect users?

## Design and verification questions

- How are lifecycle callbacks, in-flight work, resources, and state restoration coordinated under suspend/resume and process death?
- Which data belongs in ordinary local storage versus protected storage, and how are backup, deletion, and migration handled?
- How are retries, queues, caches, and media constrained by battery, memory, storage, and network availability?
- Which behaviors require a physical device, and which can be verified in a simulator? Record device/OS or simulator details for evidence.
- Test permission grant/denial/revocation, offline transitions, restoration, orientation, and accessibility paths that the feature changes.
