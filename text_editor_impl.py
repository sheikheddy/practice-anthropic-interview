import typing as tp

class TextEditorImpl:
    """
    Implements a simplified text editor with undo/redo functionality.
    
    The editor maintains state for the document text, cursor position,
    text selection, and a clipboard. All state-modifying operations
    are recorded in a history list to enable undo and redo.
    """
    
    def __init__(self):
        """Initializes the text editor to an empty state."""
        # Core state variables
        self._doc: str = ""
        self._cursor: int = 0
        self._selection: tp.Tuple[int, int] = (-1, -1)
        self._clipboard: tp.Optional[str] = None

        # Multi-document support (Level 4)
        self._documents: dict[str, tp.Tuple[str, int, tp.Tuple[int, int], dict[int, tp.Tuple[str, int, tp.Tuple[int, int]]], int, bool]] = {}
        self._current: tp.Optional[str] = None

        # History variables for undo/redo (Level 3)
        self._version: int = 0
        # History stores tuples of the entire editor state: (doc, cursor, selection)
        self._history: tp.Dict[int, tp.Tuple[str, int, tp.Tuple[int, int]]] = {
            0: (self._doc, self._cursor, self._selection)
        }
        self._can_redo: bool = False

    def _save_document(self):
        """Persists the current document state if a document is selected."""
        if self._current is None:
            return
        self._documents[self._current] = (
            self._doc,
            self._cursor,
            self._selection,
            self._history,
            self._version,
            self._can_redo,
        )

    def _load_document(self, name: str):
        """Loads the document state into the editor."""
        self._doc, self._cursor, self._selection, self._history, self._version, self._can_redo = self._documents[name]

    def _save_state(self):
        """Saves the current editor state to the history for undo/redo."""
        # If a new action is taken after an undo, the previous "future" is erased.
        if self._can_redo:
            keys_to_delete = [k for k in self._history if k > self._version]
            for k in keys_to_delete:
                del self._history[k]
        
        self._version += 1
        self._history[self._version] = (self._doc, self._cursor, self._selection)
        self._can_redo = False

    def append(self, text: str) -> str:
        """
        Appends text. If a selection exists, it replaces the selected text.
        Otherwise, it inserts the text at the cursor position.
        """
        start, end = self._selection
        if start != -1:  # A selection exists
            self._doc = self._doc[:start] + text + self._doc[end:]
            self._cursor = start + len(text)
            self._selection = (-1, -1)
        else:  # No selection, insert at cursor
            self._doc = self._doc[:self._cursor] + text + self._doc[self._cursor:]
            self._cursor += len(text)
        
        self._save_state()
        return self._doc

    def delete(self) -> str:
        """
        Deletes text. If a selection exists, it deletes the selected text.
        Otherwise, it deletes the character after the cursor.
        """
        start, end = self._selection
        if start != -1:  # A selection exists
            self._doc = self._doc[:start] + self._doc[end:]
            self._cursor = start
            self._selection = (-1, -1)
        elif self._cursor < len(self._doc):  # No selection, delete one char
            self._doc = self._doc[:self._cursor] + self._doc[self._cursor + 1:]
        
        self._save_state()
        return self._doc

    def move(self, offset: int) -> str:
        """Moves the cursor to a specific offset and clears any selection."""
        offset = int(offset)
        # Clamp the cursor position within the valid range [0, len(doc)]
        self._cursor = max(0, min(offset, len(self._doc)))
        self._selection = (-1, -1)
        
        self._save_state()
        return self._doc

    def select(self, start: int, end: int) -> str:
        """Selects a portion of the text from a start to an end index."""
        self._selection = (int(start), int(end))
        self._cursor = int(end)
        
        self._save_state()
        return self._doc

    def cut(self) -> str:
        """Cuts the selected text to the clipboard."""
        start, end = self._selection
        if start == -1:  # No selection, do nothing
            return self._doc
            
        self._clipboard = self._doc[start:end]
        self._doc = self._doc[:start] + self._doc[end:]
        self._cursor = start
        self._selection = (-1, -1)
        
        self._save_state()
        return self._doc

    def paste(self) -> str:
        """Pastes the clipboard content at the cursor position."""
        if self._clipboard is None:  # Empty clipboard, do nothing
            return self._doc
            
        self._doc = self._doc[:self._cursor] + self._clipboard + self._doc[self._cursor:]
        self._cursor += len(self._clipboard)
        
        self._save_state()
        return self._doc

    def undo(self) -> str:
        """Reverts the editor to the state before the last operation."""
        if self._version > 0:
            self._version -= 1
            self._doc, self._cursor, self._selection = self._history[self._version]
            self._can_redo = True
        
        return self._doc

    def redo(self) -> str:
        """
        Re-applies an undone operation. This is only possible if no new
        operations were performed after the UNDO.
        """
        if self._can_redo and (self._version + 1) in self._history:
            self._version += 1
            self._doc, self._cursor, self._selection = self._history[self._version]
        
        # If we reach the end of the redo chain, we can't redo further.
        if (self._version + 1) not in self._history:
            self._can_redo = False

        return self._doc

    # ------------------------------------------------------------------
    # Level 4: Multi-document support
    # ------------------------------------------------------------------

    def create(self, name: str) -> str:
        """Creates or opens a document with the given name."""
        self._save_document()

        if name in self._documents:
            self._current = name
            self._load_document(name)
            return self._doc

        self._current = name
        self._doc = ""
        self._cursor = 0
        self._selection = (-1, -1)
        self._history = {0: (self._doc, self._cursor, self._selection)}
        self._version = 0
        self._can_redo = False
        self._documents[name] = (
            self._doc,
            self._cursor,
            self._selection,
            self._history,
            self._version,
            self._can_redo,
        )
        return self._doc

    def switch(self, name: str) -> str | None:
        """Switches to an existing document by name."""
        self._save_document()
        if name not in self._documents:
            return None
        self._current = name
        self._load_document(name)
        return self._doc
