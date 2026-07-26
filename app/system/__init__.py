"""
System Package
---------------
- Owns OS-level integration that is not domain logic (Windows registry, startup).
- Isolated here so platform-specific code (winreg) doesn't leak into core/UI.
- Modules: startup (Windows "run on boot" registration).
"""
