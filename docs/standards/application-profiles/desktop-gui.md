# Desktop GUI application profile

Apply this profile to an affected component whose application types include `desktop-gui`. It supplements the base specification and design standards with GUI-specific questions.

## Specification questions

- Which user actions, keyboard shortcuts, focus transitions, and IME input are observable, including invalid or interrupted input?
- What accessibility roles, names, states, keyboard operation, and assistive-technology behavior are supported?
- How do window, dialog, view, resize, DPI, display-scale, and multi-monitor changes affect layout and state?
- Which platform or rendering-backend differences are supported or intentionally constrained?

## Design and verification questions

- Which thread owns UI objects and event dispatch, and how are work items marshalled to that thread?
- Who creates and destroys windows, views, renderers, graphics resources, and callbacks? What happens during close, restart, and partial initialization?
- How are focus, IME composition, pointer capture, keyboard navigation, and accessibility state kept synchronized?
- How are layout and rendering checked at supported scale factors and display configurations?
- Which GUI automation checks, screenshots, or manual evidence demonstrate the user-visible behavior? Record the platform/backend used and distinguish screenshots from behavioral assertions.
