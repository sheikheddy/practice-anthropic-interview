import inspect
import os
import sys
# Standard boilerplate to ensure the banking_system_impl module can be found
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
# Import your banking system implementation
from banking_system_impl import BankingSystemImpl

class BankingSystemTests(unittest.TestCase):
    """
    Test suite for the BankingSystem implementation, covering Levels 1, 2, and 3.
    """

    failureException = Exception

    def setUp(self):
        """
        This method is called before each test function.
        It creates a new, clean instance of the banking system for each test.
        """
        self.banking_system = BankingSystemImpl()

    # --------------------------------------------------------------------------
    # Level 1 Tests: Account Creation, Deposit, and Transfer
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level1_create_account_success_and_failure(self):
        """Tests successful creation and handling of duplicate accounts."""
        # Arrange, Act, Assert
        self.assertTrue(self.banking_system.create_account(1, "acc1"), "Should successfully create a new account.")
        self.assertFalse(self.banking_system.create_account(2, "acc1"), "Should fail to create a duplicate account.")

    @timeout(0.4)
    def test_level1_deposit_to_existing_and_non_existing_account(self):
        """Tests depositing into valid and invalid accounts."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        
        # Act & Assert
        self.assertEqual(self.banking_system.deposit(2, "acc1", 1000), 1000, "Deposit should return the new balance.")
        self.assertEqual(self.banking_system.deposit(3, "acc1", 500), 1500, "Subsequent deposit should be cumulative.")
        self.assertIsNone(self.banking_system.deposit(4, "non-existing", 500), "Deposit to a non-existing account should return None.")

    @timeout(0.4)
    def test_level1_transfer_successful(self):
        """Tests a valid transfer between two accounts."""
        # Arrange
        self.banking_system.create_account(1, "acc_source")
        self.banking_system.create_account(2, "acc_target")
        self.banking_system.deposit(3, "acc_source", 2000)

        # Act
        result = self.banking_system.transfer(4, "acc_source", "acc_target", 500)

        # Assert
        self.assertEqual(result, 1500, "Transfer should return the new balance of the source account.")
        # Verify target account balance by depositing 0
        self.assertEqual(self.banking_system.deposit(5, "acc_target", 0), 500, "Target account should have received the funds.")

    @timeout(0.4)
    def test_level1_transfer_insufficient_funds(self):
        """Tests transfer failure due to insufficient funds."""
        # Arrange
        self.banking_system.create_account(1, "acc_source")
        self.banking_system.create_account(2, "acc_target")
        self.banking_system.deposit(3, "acc_source", 100)

        # Act & Assert
        self.assertIsNone(self.banking_system.transfer(4, "acc_source", "acc_target", 101), "Transfer should fail and return None for insufficient funds.")
        self.assertEqual(self.banking_system.deposit(5, "acc_source", 0), 100, "Source balance should be unchanged after failed transfer.")

    @timeout(0.4)
    def test_level1_transfer_invalid_accounts(self):
        """Tests transfer failures for non-existent or identical accounts."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 1000)

        # Act & Assert
        self.assertIsNone(self.banking_system.transfer(3, "non-existing", "acc1", 100), "Transfer from a non-existing account should fail.")
        self.assertIsNone(self.banking_system.transfer(4, "acc1", "non-existing", 100), "Transfer to a non-existing account should fail.")
        self.assertIsNone(self.banking_system.transfer(5, "acc1", "acc1", 100), "Transfer to the same account should fail.")


    # --------------------------------------------------------------------------
    # Level 2 Tests: Ranking Top Spenders
    # --------------------------------------------------------------------------
    
    # Note: Assuming a method 'top_spenders(timestamp, num_accounts)' exists per Level 2 spec.
    @timeout(0.4)
    def test_level2_top_spenders_ranking(self):
        """Tests the ranking of accounts by outgoing transaction value."""
        # Arrange
        self.banking_system.create_account(1, "acc_big_spender")
        self.banking_system.create_account(2, "acc_mid_spender")
        self.banking_system.create_account(3, "acc_low_spender")
        self.banking_system.create_account(4, "acc_receiver")
        self.banking_system.deposit(5, "acc_big_spender", 1000)
        self.banking_system.deposit(6, "acc_mid_spender", 500)
        self.banking_system.deposit(7, "acc_low_spender", 100)
        
        # Act
        self.banking_system.transfer(8, "acc_big_spender", "acc_receiver", 900)
        self.banking_system.transfer(9, "acc_mid_spender", "acc_receiver", 450)
        self.banking_system.transfer(10, "acc_low_spender", "acc_receiver", 50)

        # Assert
        expected_ranking = ["acc_big_spender", "acc_mid_spender", "acc_low_spender"]
        self.assertEqual(self.banking_system.top_spenders(11, 3), expected_ranking)

    @timeout(0.4)
    def test_level2_top_spenders_with_tie_break(self):
        """Tests tie-breaking (by account_id) when spending is equal."""
        # Arrange
        self.banking_system.create_account(1, "z_spender")
        self.banking_system.create_account(2, "a_spender")
        self.banking_system.create_account(3, "acc_receiver")
        self.banking_system.deposit(4, "z_spender", 500)
        self.banking_system.deposit(5, "a_spender", 500)

        # Act
        self.banking_system.transfer(6, "z_spender", "acc_receiver", 500)
        self.banking_system.transfer(7, "a_spender", "acc_receiver", 500)

        # Assert - 'a_spender' should come before 'z_spender' due to alphabetical order
        expected_ranking = ["a_spender", "z_spender"]
        self.assertEqual(self.banking_system.top_spenders(8, 2), expected_ranking)

    @timeout(0.4)
    def test_level2_top_spenders_no_transactions(self):
        """Tests that top_spenders returns an empty list when no transfers have occurred."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 1000)
        
        # Act & Assert
        self.assertEqual(self.banking_system.top_spenders(3, 5), [])


    # --------------------------------------------------------------------------
    # Level 3 Tests: Scheduled and Canceled Payments
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level3_schedule_and_execute_payment_successful(self):
        """Tests scheduling a payment and verifying its execution."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 1000)
        
        # Act
        payment_id = self.banking_system.schedule_payment(3, "acc1", 300, 5) # Schedules payment for timestamp 3+5=8
        
        # Assert
        self.assertEqual(payment_id, "payment1")
        # Check balance before execution time
        self.assertEqual(self.banking_system.deposit(7, "acc1", 0), 1000)
        # Trigger execution by calling an operation at/after the scheduled time
        self.assertEqual(self.banking_system.deposit(8, "acc1", 0), 700, "Balance should be reduced after payment execution.")

    @timeout(0.4)
    def test_level3_schedule_payment_insufficient_funds_at_execution(self):
        """Tests that a scheduled payment is skipped if funds are insufficient at execution time."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 100)
        
        # Act
        self.banking_system.schedule_payment(3, "acc1", 200, 5) # Schedules for timestamp 8
        
        # Assert
        # Trigger execution and check balance
        self.assertEqual(self.banking_system.deposit(8, "acc1", 0), 100, "Balance should be unchanged as payment was skipped.")

    @timeout(0.4)
    def test_level3_cancel_payment_successful(self):
        """Tests successfully canceling a scheduled payment before it executes."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 1000)
        payment_id = self.banking_system.schedule_payment(3, "acc1", 500, 10) # Executes at timestamp 13

        # Act & Assert
        self.assertTrue(self.banking_system.cancel_payment(5, "acc1", payment_id), "Should return True for successful cancellation.")
        # Trigger time past execution and check balance
        self.assertEqual(self.banking_system.deposit(13, "acc1", 0), 1000, "Balance should be unchanged for a canceled payment.")

    @timeout(0.4)
    def test_level3_cancel_payment_failure_cases(self):
        """Tests various failure scenarios for canceling a payment."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.create_account(2, "acc2")
        self.banking_system.deposit(3, "acc1", 1000)
        payment_id = self.banking_system.schedule_payment(4, "acc1", 500, 10) # Executes at timestamp 14

        # Act & Assert
        self.assertFalse(self.banking_system.cancel_payment(5, "acc2", payment_id), "Should fail to cancel from wrong account.")
        self.assertFalse(self.banking_system.cancel_payment(6, "acc1", "invalid_id"), "Should fail to cancel non-existent payment.")
        
        # Cancel once successfully
        self.assertTrue(self.banking_system.cancel_payment(7, "acc1", payment_id))
        # Try to cancel again
        self.assertFalse(self.banking_system.cancel_payment(8, "acc1", payment_id), "Should fail to cancel an already-canceled payment.")
    
    @timeout(0.4)
    def test_level3_payment_executes_before_cancel_at_same_timestamp(self):
        """Tests that at a given timestamp, payments are processed before cancellations."""
        # Arrange
        self.banking_system.create_account(1, "acc1")
        self.banking_system.deposit(2, "acc1", 500)
        payment_id = self.banking_system.schedule_payment(3, "acc1", 100, 5) # Executes at timestamp 8
        
        # Act & Assert
        # At timestamp 8, the payment should execute first, then the cancellation is attempted.
        self.assertFalse(self.banking_system.cancel_payment(8, "acc1", payment_id), "Cancel should fail as payment has already executed.")
        # Verify the payment was indeed made
        self.assertEqual(self.banking_system.deposit(9, "acc1", 0), 400)

    @timeout(0.4)
    def test_level3_top_spenders_includes_scheduled_payments(self):
        """Tests that successful scheduled payments are included in top_spenders ranking."""
        # Arrange
        self.banking_system.create_account(1, "acc_transfer_spender")
        self.banking_system.create_account(2, "acc_payment_spender")
        self.banking_system.create_account(3, "acc_receiver")
        self.banking_system.deposit(4, "acc_transfer_spender", 1000)
        self.banking_system.deposit(5, "acc_payment_spender", 1000)

        # Act
        # Spender 1 uses a regular transfer
        self.banking_system.transfer(6, "acc_transfer_spender", "acc_receiver", 500)
        # Spender 2 uses a scheduled payment of a larger amount
        self.banking_system.schedule_payment(7, "acc_payment_spender", 800, 5) # Executes at ts 12

        # Trigger payment execution
        self.banking_system.deposit(12, "acc_payment_spender", 0)

        # Assert
        expected_ranking = ["acc_payment_spender", "acc_transfer_spender"]
        self.assertEqual(self.banking_system.top_spenders(13, 2), expected_ranking)
        
from file_storage_system_impl import FileStorageSystemImpl


class FileStorageSystemTests(unittest.TestCase):
    """
    Test suite for the FileStorageSystem implementation, covering Levels 1, 2, and 3.
    """

    failureException = Exception

    def setUp(self):
        """
        This method is called before each test function.
        It creates a new, clean instance of the file storage system for each test.
        """
        self.file_system = FileStorageSystemImpl()

    # --------------------------------------------------------------------------
    # Level 1 Tests: Basic File Operations
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level1_add_file_success_and_failure(self):
        """Tests successful creation and handling of duplicate files."""
        # Arrange, Act, Assert
        self.assertEqual(self.file_system.add_file("/home/user/file.txt", 100), "true", "Should successfully create a new file.")
        self.assertEqual(self.file_system.add_file("/home/user/file.txt", 200), "false", "Should fail to create a duplicate file.")

    @timeout(0.4)
    def test_level1_get_file_size_existing_and_non_existing(self):
        """Tests retrieving the size of valid and invalid files."""
        # Arrange
        self.file_system.add_file("/data/log.csv", 512)
        
        # Act & Assert
        self.assertEqual(self.file_system.get_file_size("/data/log.csv"), "512", "Should return the correct size for an existing file.")
        self.assertEqual(self.file_system.get_file_size("/data/non_existing.log"), "", "Should return an empty string for a non-existing file.")

    @timeout(0.4)
    def test_level1_delete_file_success_and_failure(self):
        """Tests a valid deletion and an attempt to delete a non-existent file."""
        # Arrange
        self.file_system.add_file("/tmp/temp_file", 42)

        # Act & Assert
        self.assertEqual(self.file_system.delete_file("/tmp/temp_file"), "42", "Delete should return the size of the deleted file.")
        # Verify the file is gone
        self.assertEqual(self.file_system.get_file_size("/tmp/temp_file"), "", "File should not exist after deletion.")
        # Test deleting a non-existent file
        self.assertEqual(self.file_system.delete_file("/tmp/non_existent"), "false", "Deleting a non-existent file should return 'false'.")

    # --------------------------------------------------------------------------
    # Level 2 Tests: Querying and Ranking Files
    # --------------------------------------------------------------------------
    
    @timeout(0.4)
    def test_level2_get_n_files_by_prefix_ranking(self):
        """Tests the ranking of files by size (desc) and then path (asc)."""
        # Arrange
        self.file_system.add_file("/media/photos/cat.jpg", 2048)
        self.file_system.add_file("/media/videos/holiday.mp4", 51200)
        self.file_system.add_file("/media/photos/dog.png", 4096)
        self.file_system.add_file("/other/unrelated.txt", 100)
        
        # Act
        result = self.file_system.get_n_files_by_prefix("/media/", 3)

        # Assert
        expected = "/media/videos/holiday.mp4(51200), /media/photos/dog.png(4096), /media/photos/cat.jpg(2048)"
        self.assertEqual(result, expected, "Should return top 3 files under prefix, sorted by size.")

    @timeout(0.4)
    def test_level2_get_n_files_by_prefix_with_tie_break(self):
        """Tests tie-breaking (by file_path) when file sizes are equal."""
        # Arrange
        self.file_system.add_file("/docs/report_z.pdf", 1500)
        self.file_system.add_file("/docs/report_a.pdf", 1500)
        self.file_system.add_file("/docs/summary.txt", 1000)

        # Act
        result = self.file_system.get_n_files_by_prefix("/docs/", 3)

        # Assert - 'report_a.pdf' should come before 'report_z.pdf' due to lexicographical order
        expected = "/docs/report_a.pdf(1500), /docs/report_z.pdf(1500), /docs/summary.txt(1000)"
        self.assertEqual(result, expected, "Tie in size should be broken by file path ascending.")

    @timeout(0.4)
    def test_level2_get_n_files_by_prefix_edge_cases(self):
        """Tests scenarios with no matching files or when count exceeds matches."""
        # Arrange
        self.file_system.add_file("/a/b/c.txt", 10)
        
        # Act & Assert
        self.assertEqual(self.file_system.get_n_files_by_prefix("/x/y/", 5), "", "Should return empty string for a non-matching prefix.")
        self.assertEqual(self.file_system.get_n_files_by_prefix("/a/", 10), "/a/b/c.txt(10)", "Should return all matches if count is larger than available files.")

    # --------------------------------------------------------------------------
    # Level 3 Tests: User Management and Capacity
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level3_add_user_and_add_file_by_user(self):
        """Tests creating a user and adding a file, checking capacity reduction."""
        # Arrange
        self.assertEqual(self.file_system.add_user("user1", 1000), "true")
        
        # Act & Assert
        self.assertEqual(self.file_system.add_file_by_user("/home/user1/data.bin", "user1", 400), "600", "Should return remaining capacity.")
        self.assertEqual(self.file_system.add_file_by_user("/home/user1/big_data.bin", "user1", 700), "", "Should fail due to insufficient capacity.")
        self.assertEqual(self.file_system.add_file_by_user("/home/user1/another.txt", "non_existent_user", 100), "", "Should fail for non-existent user.")

    @timeout(0.4)
    def test_level3_delete_file_restores_user_capacity(self):
        """Tests that deleting a user's file correctly restores their capacity."""
        # Arrange
        self.file_system.add_user("user2", 50)
        self.file_system.add_file_by_user("/files/a.txt", "user2", 40) # Remaining capacity: 10
        
        # Act
        self.file_system.delete_file("/files/a.txt") # Capacity should be restored to 50
        
        # Assert
        # This file would fail before the delete (30 > 10), but should succeed now (30 < 50)
        self.assertEqual(self.file_system.add_file_by_user("/files/b.txt", "user2", 30), "20", "Capacity should be restored after deletion.")

    @timeout(0.4)
    def test_level3_merge_users_success(self):
        """Tests successfully merging two users."""
        # Arrange
        self.file_system.add_user("target_user", 100)
        self.file_system.add_user("source_user", 200)
        self.file_system.add_file_by_user("/target/file.txt", "target_user", 60) # target_user has 40 left
        self.file_system.add_file_by_user("/source/file.txt", "source_user", 50) # source_user has 150 left

        # Act
        result = self.file_system.merge_users("target_user", "source_user")

        # Assert
        self.assertEqual(result, "190", "New capacity should be the sum of remaining capacities (40 + 150).")
        # Verify source user's file is now owned by target
        self.assertEqual(self.file_system.get_file_size("/source/file.txt"), "50")
        # Verify source user is deleted
        self.assertEqual(self.file_system.add_file_by_user("/new/file.txt", "source_user", 10), "", "Source user should no longer exist.")

    @timeout(0.4)
    def test_level3_merge_users_failure_cases(self):
        """Tests various failure scenarios for merging users."""
        # Arrange
        self.file_system.add_user("userA", 100)
        
        # Act & Assert
        self.assertEqual(self.file_system.merge_users("userA", "non_existent"), "", "Should fail if source user does not exist.")
        self.assertEqual(self.file_system.merge_users("non_existent", "userA"), "", "Should fail if target user does not exist.")
        self.assertEqual(self.file_system.merge_users("userA", "userA"), "", "Should fail if source and target users are the same.")

from text_editor_impl import TextEditorImpl

class TextEditorTests(unittest.TestCase):
    """
    Test suite for the TextEditor implementation, covering Levels 1, 2, and 3.
    """

    failureException = Exception

    def setUp(self):
        """
        This method is called before each test function.
        It creates a new, clean instance of the text editor for each test.
        """
        self.editor = TextEditorImpl()

    def run_queries(self, queries):
        """Helper function to run a sequence of operations."""
        results = []
        for query in queries:
            op_name = query[0].lower()
            args = query[1:]
            method = getattr(self.editor, op_name)
            results.append(method(*args))
        return results

    # --------------------------------------------------------------------------
    # Level 1 Tests: Append, Move, and Delete
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level1_append_and_move(self):
        """Tests basic text appending and cursor movement."""
        # Arrange, Act, Assert
        self.assertEqual(self.editor.append("Hello"), "Hello", "Should append to an empty document.")
        self.assertEqual(self.editor.append(", World"), "Hello, World", "Should append to existing text.")
        # Move does not change the document content
        self.assertEqual(self.editor.move(0), "Hello, World", "Move should not alter the document.")

    @timeout(0.4)
    def test_level1_delete_character(self):
        """Tests deleting characters at different cursor positions."""
        # Arrange
        self.editor.append("abcde")

        # Act & Assert
        self.editor.move(2) # Cursor after 'b'
        self.assertEqual(self.editor.delete(), "abde", "Should delete the character 'c' at the cursor's position.")
        self.editor.move(0) # Cursor at the start
        self.assertEqual(self.editor.delete(), "bde", "Should delete the first character.")

    @timeout(0.4)
    def test_level1_move_and_delete_edge_cases(self):
        """Tests moving the cursor to boundaries and deleting from the end."""
        # Arrange
        self.editor.append("edge")

        # Act & Assert
        # Move cursor past the end of the document
        self.editor.move(10)
        self.assertEqual(self.editor.delete(), "edge", "Deleting past the end should have no effect.")
        # Move cursor to the exact end
        self.editor.move(4)
        self.assertEqual(self.editor.delete(), "edge", "Deleting at the exact end should have no effect.")
        # Move cursor to a negative position (should be treated as 0)
        self.editor.move(-5)
        self.assertEqual(self.editor.delete(), "dge", "Deleting after a negative move should delete the first character.")

    # --------------------------------------------------------------------------
    # Level 2 Tests: Selection, Cut, and Paste
    # --------------------------------------------------------------------------
    
    @timeout(0.4)
    def test_level2_select_and_delete(self):
        """Tests deleting a selected portion of text."""
        # Arrange
        self.editor.append("Hello, beautiful World!")
        
        # Act
        self.editor.select(7, 17) # Select "beautiful "
        result = self.editor.delete()

        # Assert
        self.assertEqual(result, "Hello, World!", "Should delete the selected text.")
    
    @timeout(0.4)
    def test_level2_select_and_replace_with_append(self):
        """Tests replacing a selected portion of text using APPEND."""
        # Arrange
        self.editor.append("This is an old sentence.")
        
        # Act
        self.editor.select(11, 14) # Select "old"
        result = self.editor.append("new")

        # Assert
        self.assertEqual(result, "This is an new sentence.", "APPEND should replace the selected text.")

    @timeout(0.4)
    def test_level2_cut_and_paste(self):
        """Tests the full cut-and-paste workflow."""
        # Arrange
        self.editor.append("second first")
        
        # Act
        self.editor.select(7, 12) # Select "first"
        cut_result = self.editor.cut()
        self.editor.move(0)
        paste_result = self.editor.paste()

        # Assert
        self.assertEqual(cut_result, "second ", "Cut should remove the selected text.")
        self.assertEqual(paste_result, "firstsecond ", "Paste should insert the cut text at the cursor.")

    @timeout(0.4)
    def test_level2_clipboard_operations_edge_cases(self):
        """Tests cut/paste when nothing is selected or clipboard is empty."""
        # Arrange
        self.editor.append("Some text")

        # Act & Assert
        self.assertEqual(self.editor.cut(), "Some text", "Cut with no selection should not change the document.")
        self.assertEqual(self.editor.paste(), "Some text", "Paste with an empty clipboard should not change the document.")
        # Now, cut something to populate clipboard
        self.editor.select(0, 5)
        self.editor.cut() # Document is "text", clipboard is "Some "
        self.editor.move(0)
        self.editor.paste() # Document is "Some text"
        self.assertEqual(self.editor.paste(), "Some Some text", "Pasting multiple times should be possible.")

    # --------------------------------------------------------------------------
    # Level 3 Tests: Undo and Redo
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level3_simple_undo_and_redo(self):
        """Tests a simple sequence of operations, followed by undo and redo."""
        # Arrange & Act
        results = self.run_queries([
            ["APPEND", "Hello"],     # "Hello"
            ["APPEND", " World"],    # "Hello World"
            ["UNDO"],                # "Hello"
            ["UNDO"],                # ""
            ["REDO"],                # "Hello"
            ["REDO"]                 # "Hello World"
        ])
        
        # Assert
        self.assertEqual(results, ["Hello", "Hello World", "Hello", "", "Hello", "Hello World"])

    @timeout(0.4)
    def test_level3_redo_is_invalidated_by_new_operation(self):
        """Tests that a new operation after an UNDO clears the redo history."""
        # Arrange & Act
        results = self.run_queries([
            ["APPEND", "A"],         # "A"
            ["APPEND", "B"],         # "AB"
            ["UNDO"],                # "A"
            ["APPEND", "C"],         # "AC"
            ["REDO"]                 # Should do nothing, as the 'APPEND "C"' invalidated the redo of 'APPEND "B"'
        ])
        
        # Assert
        self.assertEqual(results[-1], "AC", "REDO should have no effect after a new operation.")
        self.assertEqual(results, ["A", "AB", "A", "AC", "AC"])

    @timeout(0.4)
    def test_level3_undo_redo_out_of_bounds(self):
        """Tests calling UNDO or REDO when there's no history to act upon."""
        # Arrange & Act
        results = self.run_queries([
            ["APPEND", "start"],     # "start"
            ["REDO"],                # "start" (no effect)
            ["UNDO"],                # ""
            ["UNDO"],                # "" (no effect)
            ["REDO"]                 # "start"
        ])

        # Assert
        self.assertEqual(results, ["start", "start", "", "", "start"])

    @timeout(0.4)
    def test_level3_undo_restores_full_state(self):
        """Tests that UNDO restores cursor position and selection, not just text."""
        # Arrange
        self.editor.append("Test text")
        self.editor.select(0, 4) # Select "Test"
        
        # Act
        self.editor.undo() # Should revert to before the SELECT call
        
        # Assert
        # After undoing SELECT, there should be no selection. APPEND should insert at the cursor's
        # last position (end of the string), not replace anything.
        final_state = self.editor.append("!")
        self.assertEqual(final_state, "Test text!", "Appending should happen at the end, proving selection was undone.")

from time_tracking_system_impl import TimeTrackingSystemImpl

class TimeTrackingSystemTests(unittest.TestCase):
    """
    Test suite for the TimeTrackingSystem implementation, covering Levels 1, 2, and 3.
    """

    failureException = Exception

    def setUp(self):
        """
        This method is called before each test function.
        It creates a new, clean instance of the system for each test.
        """
        self.system = TimeTrackingSystemImpl()

    # --------------------------------------------------------------------------
    # Level 1 Tests: Add Worker, Register Time, and Get Total Time
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level1_add_worker_success_and_failure(self):
        """Tests successful creation and handling of duplicate workers."""
        # Arrange, Act, Assert
        self.assertTrue(self.system.add_worker("w1", "Developer", 100), "Should successfully add a new worker.")
        self.assertFalse(self.system.add_worker("w1", "QA", 80), "Should fail to add a duplicate worker.")

    @timeout(0.4)
    def test_level1_register_and_get_work_time(self):
        """Tests registering work sessions and getting the cumulative time."""
        # Arrange
        self.system.add_worker("ashley", "Developer", 150)
        
        # Act & Assert
        self.assertEqual(self.system.register(10, "ashley"), "registered", "First register should be successful.")
        self.assertEqual(self.system.register(25, "ashley"), "registered", "Second register should be successful.")
        self.assertEqual(self.system.get("ashley"), "15", "Total time should be 15 after one session.")

        # Second session
        self.system.register(40, "ashley")
        self.system.register(70, "ashley")
        self.assertEqual(self.system.get("ashley"), "45", "Total time should be cumulative (15 + 30).")
        
        # Invalid requests
        self.assertEqual(self.system.register(100, "non-existent"), "invalid_request", "Register for a non-existent worker should fail.")
        self.assertEqual(self.system.get("non-existent"), "", "Get for a non-existent worker should return an empty string.")

    @timeout(0.4)
    def test_level1_get_work_time_edge_cases(self):
        """Tests 'get' for workers with no sessions or incomplete sessions."""
        # Arrange
        self.system.add_worker("w1", "Analyst", 120)
        
        # Act & Assert
        self.assertEqual(self.system.get("w1"), "", "Should return empty string for a worker with no sessions.")
        
        # Register a clock-in but no clock-out
        self.system.register(100, "w1")
        self.assertEqual(self.system.get("w1"), "", "Should return empty string for an incomplete session.")

    # --------------------------------------------------------------------------
    # Level 2 Tests: Ranking Top Workers
    # --------------------------------------------------------------------------
    
    @timeout(0.4)
    def test_level2_top_n_workers_ranking(self):
        """Tests the ranking of workers by total time worked in a position."""
        # Arrange
        self.system.add_worker("john", "Developer", 150)
        self.system.add_worker("jane", "Developer", 160)
        self.system.add_worker("bob", "Developer", 140)
        self.system.add_worker("sara", "QA", 100) # Different position
        
        # Act
        self.system.register(10, "john"); self.system.register(60, "john") # 50
        self.system.register(10, "jane"); self.system.register(110, "jane") # 100
        self.system.register(10, "bob"); self.system.register(30, "bob") # 20
        self.system.register(10, "sara"); self.system.register(200, "sara") # 190

        # Assert
        expected_ranking = "jane(100), john(50), bob(20)"
        self.assertEqual(self.system.top_n_workers(3, "Developer"), expected_ranking)
        self.assertEqual(self.system.top_n_workers(1, "QA"), "sara(190)")

    @timeout(0.4)
    def test_level2_top_n_workers_with_tie_break(self):
        """Tests tie-breaking (by worker_id) when work time is equal."""
        # Arrange
        self.system.add_worker("zulu", "Analyst", 100)
        self.system.add_worker("alpha", "Analyst", 100)

        # Act
        self.system.register(10, "zulu"); self.system.register(60, "zulu") # 50
        self.system.register(100, "alpha"); self.system.register(150, "alpha") # 50

        # Assert - 'alpha' should come before 'zulu' due to alphabetical order
        expected_ranking = "alpha(50), zulu(50)"
        self.assertEqual(self.system.top_n_workers(2, "Analyst"), expected_ranking)

    @timeout(0.4)
    def test_level2_top_n_workers_no_work_time(self):
        """Tests that top_n_workers handles workers with no completed sessions and empty positions."""
        # Arrange
        self.system.add_worker("w1", "Designer", 100)
        
        # Act & Assert
        self.assertEqual(self.system.top_n_workers(5, "Designer"), "w1(0)")
        self.assertEqual(self.system.top_n_workers(5, "Developer"), "")


    # --------------------------------------------------------------------------
    # Level 3 Tests: Promotions and Salary Calculation
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level3_promote_and_verify_activation(self):
        """Tests scheduling a promotion and verifying its activation upon a register event."""
        # Arrange
        self.system.add_worker("w1", "Junior Developer", 100)
        
        # Act
        # Schedule promotion to be effective at timestamp 200
        result = self.system.promote("w1", "Senior Developer", 200, 200)
        
        # Assert
        self.assertEqual(result, "success")
        # Register before effective time, worker should not be in the new role yet
        self.system.register(150, "w1")
        self.assertEqual(self.system.top_n_workers(1, "Senior Developer"), "")
        
        # Register at effective time, triggering the promotion
        self.system.register(200, "w1")
        self.assertEqual(self.system.top_n_workers(1, "Senior Developer"), "w1(0)", "Worker should now be in the new position.")

    @timeout(0.4)
    def test_level3_promote_failure_cases(self):
        """Tests failure scenarios for scheduling a promotion."""
        # Arrange
        self.system.add_worker("w1", "Developer", 150)

        # Act & Assert
        self.assertEqual(self.system.promote("non-existent", "Lead", 300, 100), "invalid_request", "Should fail for non-existent worker.")
        
        # Schedule one promotion
        self.system.promote("w1", "Senior Developer", 200, 200)
        # Try to schedule another before the first is activated
        self.assertEqual(self.system.promote("w1", "Architect", 300, 300), "invalid_request", "Should fail if a promotion is already pending.")

    @timeout(0.4)
    def test_level3_calc_salary_with_promotion(self):
        """Tests salary calculation for a worker whose compensation changes mid-period."""
        # Arrange
        self.system.add_worker("w1", "Junior Developer", 100) # Rate: 100
        self.system.promote("w1", "Senior Developer", 200, 200) # New rate: 200, effective at ts=200
        
        # Act
        # Work session from 150 to 250, spanning the promotion
        self.system.register(150, "w1")
        self.system.register(200, "w1") # This register activates the promotion
        self.system.register(250, "w1")

        # Assert
        # Salary from 150 to 200 is (200-150)*100 = 5000
        # Salary from 200 to 250 is (250-200)*200 = 10000
        # Total = 15000
        self.assertEqual(self.system.calc_salary("w1", 150, 250), "15000")
        # Check a sub-period
        self.assertEqual(self.system.calc_salary("w1", 180, 220), "6000")

    @timeout(0.4)
    def test_level3_top_n_workers_uses_time_in_current_position_only(self):
        """Tests that top_n_workers ranking is based only on time since the last promotion."""
        # Arrange
        self.system.add_worker("w1", "Junior", 100)
        
        # Act
        # Work 50 hours as Junior
        self.system.register(10, "w1"); self.system.register(60, "w1")
        self.assertEqual(self.system.top_n_workers(1, "Junior"), "w1(50)")
        
        # Promote to Senior, effective at 100
        self.system.promote("w1", "Senior", 200, 100)
        self.system.register(100, "w1") # Activate promotion
        
        # Work 20 hours as Senior
        self.system.register(110, "w1"); self.system.register(130, "w1")
        
        # Assert
        # Should have 0 time in Junior role now for ranking purposes
        self.assertEqual(self.system.top_n_workers(1, "Junior"), "")
        # Should have 20 time in Senior role
        self.assertEqual(self.system.top_n_workers(1, "Senior"), "w1(20)")
        # The 'get' method should still return total time
        self.assertEqual(self.system.get("w1"), "70") # 50 + 20
        
from course_system_impl import CourseSystemImpl

class Level1Tests(unittest.TestCase):
    """
    Tests for Level 1: Course Creation and Student Registration.
    """
    failureException = Exception

    def setUp(self):
        """Set up a new, empty system before each test."""
        self.system = CourseSystemImpl()

    @timeout(0.5)
    def test_create_course_success(self):
        self.assertTrue(self.system.create_course("CS101", "Intro to CS", 4))
        self.assertTrue(self.system.create_course("MA201", "Calculus I", 3))

    @timeout(0.5)
    def test_create_course_duplicate_id(self):
        self.assertTrue(self.system.create_course("CS101", "Intro to CS", 4))
        self.assertFalse(self.system.create_course("CS101", "Advanced CS", 4), "Should fail with duplicate course ID")

    @timeout(0.5)
    def test_create_course_duplicate_name(self):
        self.assertTrue(self.system.create_course("CS101", "Intro to CS", 4))
        self.assertFalse(self.system.create_course("CS102", "Intro to CS", 4), "Should fail with duplicate course name")

    @timeout(0.5)
    def test_register_new_student_success(self):
        self.system.create_course("CS101", "Intro to CS", 4)
        self.assertEqual(self.system.register_for_course("student1", "CS101"), "20", "New student should have 24 credits initially")

    @timeout(0.5)
    def test_register_for_nonexistent_course(self):
        self.assertEqual(self.system.register_for_course("student1", "CS999"), "", "Should fail for non-existent course")

    @timeout(0.5)
    def test_register_student_already_registered(self):
        self.system.create_course("CS101", "Intro to CS", 4)
        self.system.register_for_course("student1", "CS101")
        self.assertEqual(self.system.register_for_course("student1", "CS101"), "", "Should fail if student is already registered")

    @timeout(0.5)
    def test_register_insufficient_credits(self):
        self.system.create_course("ENG400", "Advanced Literature", 20)
        self.system.create_course("PHY300", "Quantum Mechanics", 5)
        self.system.register_for_course("student1", "ENG400") # Remaining credits: 4
        self.assertEqual(self.system.register_for_course("student1", "PHY300"), "", "Should fail due to insufficient credits")


class Level2Tests(unittest.TestCase):
    """
    Tests for Level 2: Finding Paired Students.
    """
    failureException = Exception

    def setUp(self):
        """Set up a system with courses and students for pairing tests."""
        self.system = CourseSystemImpl()
        self.system.create_course("CS101", "Intro to CS", 4)
        self.system.create_course("MA201", "Calculus I", 3)
        self.system.create_course("PHY101", "Physics", 4)

    @timeout(0.5)
    def test_get_pairs_no_pairs(self):
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "MA201")
        self.assertEqual(self.system.get_paired_students(), "")

    @timeout(0.5)
    def test_get_pairs_one_course_simple_pair(self):
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.assertEqual(self.system.get_paired_students(), "[[Alice, Bob]]")

    @timeout(0.5)
    def test_get_pairs_one_course_multiple_students(self):
        self.system.register_for_course("Charlie", "CS101")
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        # Expected pairs: (Alice, Bob), (Alice, Charlie), (Bob, Charlie)
        expected = "[[Alice, Bob], [Alice, Charlie], [Bob, Charlie]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.5)
    def test_get_pairs_multiple_courses_and_sorting(self):
        # CS101: Alice, Bob
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("Alice", "CS101")
        # MA201: Charlie, Bob, Alice
        self.system.register_for_course("Charlie", "MA201")
        self.system.register_for_course("Bob", "MA201")
        self.system.register_for_course("Alice", "MA201")
        # PHY101: No pairs
        self.system.register_for_course("David", "PHY101")

        # Courses should be sorted by ID: CS101, MA201
        cs101_pairs = "[Alice, Bob]"
        ma201_pairs = "[Alice, Bob], [Alice, Charlie], [Bob, Charlie]"
        expected = f"[{cs101_pairs}], [{ma201_pairs}]"
        self.assertEqual(self.system.get_paired_students(), expected)


class Level3Tests(unittest.TestCase):
    """
    Tests for Level 3: Extended Course Types, Grading, and GPA Calculation.
    """
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()
        # Standard courses
        self.system.create_course_ext("CSE220", "Data Structures", 3, "Standard")
        self.system.create_course_ext("CSE300", "Operating Systems", 4, "Standard")
        # Pass/Fail course
        self.system.create_course_ext("CSE330", "Computer Architecture", 3, "Pass/Fail")

    @timeout(0.5)
    def test_set_component_grade_flow(self):
        self.system.register_for_course("stu001", "CSE220")
        self.assertEqual(self.system.set_component_grade("stu001", "CSE220", "midterm", 25), "set")
        self.assertEqual(self.system.set_component_grade("stu001", "CSE220", "midterm", 30), "updated")

    @timeout(0.5)
    def test_set_component_grade_invalid(self):
        self.system.register_for_course("stu001", "CSE220")
        self.assertEqual(self.system.set_component_grade("stu002", "CSE220", "final", 30), "invalid", "Student not registered")
        self.assertEqual(self.system.set_component_grade("stu001", "CSE999", "final", 30), "invalid", "Course does not exist")
        self.assertEqual(self.system.set_component_grade("stu001", "CSE300", "final", 30), "invalid", "Student not registered for this course")

    @timeout(0.5)
    def test_get_pairs_ignores_pass_fail_courses(self):
        self.system.register_for_course("stu001", "CSE330") # Pass/Fail
        self.system.register_for_course("stu002", "CSE330") # Pass/Fail
        self.assertEqual(self.system.get_paired_students(), "", "Should ignore pairs in Pass/Fail courses")

    @timeout(0.5)
    def test_get_gpa_not_enough_components(self):
        self.system.register_for_course("stu001", "CSE220")
        self.system.set_component_grade("stu001", "CSE220", "midterm", 25)
        self.system.set_component_grade("stu001", "CSE220", "final", 35)
        self.assertEqual(self.system.get_gpa("stu001"), "", "GPA should not be calculated with < 3 components")

    @timeout(0.5)
    def test_get_gpa_full_calculation(self):
        # Register student for all three courses
        self.system.register_for_course("stu002", "CSE220") # Standard, 3 credits
        self.system.register_for_course("stu002", "CSE300") # Standard, 4 credits
        self.system.register_for_course("stu002", "CSE330") # Pass/Fail, 3 credits

        # Set grades for CSE220 (Total: 25+23+33 = 81)
        self.system.set_component_grade("stu002", "CSE220", "homeworks", 25)
        self.system.set_component_grade("stu002", "CSE220", "midterm", 23)
        self.system.set_component_grade("stu002", "CSE220", "final", 33)

        # Set grades for CSE300 (Total: 20+20+35 = 75)
        self.system.set_component_grade("stu002", "CSE300", "homeworks", 20)
        self.system.set_component_grade("stu002", "CSE300", "midterm", 20)
        self.system.set_component_grade("stu002", "CSE300", "final", 35)

        # Set grades for CSE330 (Total: 25+25+15 = 65 -> Fail)
        self.system.set_component_grade("stu002", "CSE330", "homeworks", 25)
        self.system.set_component_grade("stu002", "CSE330", "midterm", 25)
        self.system.set_component_grade("stu002", "CSE330", "final", 15)

        # Weighted Average = (81*3 + 75*4) / (3+4) = (243 + 300) / 7 = 543 / 7 = 77.57 -> 77
        # Pass/Fail: 0 pass, 1 fail
        self.assertEqual(self.system.get_gpa("stu002"), "77, 0, 1")

        # Update CSE330 to pass (Total: 25+25+16 = 66 -> Pass)
        self.system.set_component_grade("stu002", "CSE330", "final", 16)
        # GPA should now be "77, 1, 0"
        self.assertEqual(self.system.get_gpa("stu002"), "77, 1, 0")
        
from database_impl import DatabaseImpl

class DatabaseTests(unittest.TestCase):
    """
    Test suite for the DatabaseImpl implementation, covering Levels 1, 2, and 3.
    """

    failureException = Exception

    def setUp(self):
        """
        This method is called before each test function.
        It creates a new, clean instance of the database for each test.
        """
        self.db = DatabaseImpl()

    # --------------------------------------------------------------------------
    # Level 1 Tests: SET, GET, and DELETE
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level1_set_and_get(self):
        """Tests setting a value and successfully retrieving it."""
        # Arrange, Act
        self.db.set("user:1", "name", "Alice")
        
        # Assert
        self.assertEqual(self.db.get("user:1", "name"), "Alice", "Should retrieve the correct value.")

    @timeout(0.4)
    def test_level1_set_overwrite(self):
        """Tests that setting an existing key-field pair overwrites the value."""
        # Arrange
        self.db.set("user:1", "status", "active")
        
        # Act
        self.db.set("user:1", "status", "inactive")
        
        # Assert
        self.assertEqual(self.db.get("user:1", "status"), "inactive", "The value should be overwritten.")

    @timeout(0.4)
    def test_level1_get_non_existent(self):
        """Tests that getting a non-existent key or field returns an empty string."""
        # Arrange
        self.db.set("user:1", "name", "Alice")
        
        # Act & Assert
        self.assertEqual(self.db.get("user:1", "email"), "", "Getting a non-existent field should return an empty string.")
        self.assertEqual(self.db.get("user:2", "name"), "", "Getting from a non-existent key should return an empty string.")

    @timeout(0.4)
    def test_level1_delete_success(self):
        """Tests successful deletion of a field."""
        # Arrange
        self.db.set("user:1", "temp_data", "to_be_deleted")

        # Act
        result = self.db.delete("user:1", "temp_data")

        # Assert
        self.assertEqual(result, "true", "Delete should return 'true' on success.")
        self.assertEqual(self.db.get("user:1", "temp_data"), "", "The value should be gone after deletion.")

    @timeout(0.4)
    def test_level1_delete_failure(self):
        """Tests that deleting a non-existent key or field fails correctly."""
        # Arrange
        self.db.set("user:1", "name", "Alice")

        # Act & Assert
        self.assertEqual(self.db.delete("user:1", "non_existent_field"), "false", "Deleting a non-existent field should return 'false'.")
        self.assertEqual(self.db.delete("user:2", "name"), "false", "Deleting from a non-existent key should return 'false'.")

    # --------------------------------------------------------------------------
    # Level 2 Tests: SCAN and SCAN_BY_PREFIX
    # --------------------------------------------------------------------------
    
    @timeout(0.4)
    def test_level2_scan_returns_sorted_records(self):
        """Tests that SCAN retrieves all records for a key, sorted alphabetically by field."""
        # Arrange
        self.db.set("user:1", "name", "Alice")
        self.db.set("user:1", "city", "New York")
        self.db.set("user:1", "age", "30")

        # Act
        result = self.db.scan("user:1")

        # Assert
        expected = "age(30), city(New York), name(Alice)"
        self.assertEqual(result, expected, "SCAN result should be correctly formatted and sorted.")

    @timeout(0.4)
    def test_level2_scan_by_prefix(self):
        """Tests retrieving records that match a specific field prefix."""
        # Arrange
        self.db.set("user:1", "contact:email", "alice@example.com")
        self.db.set("user:1", "personal:name", "Alice")
        self.db.set("user:1", "contact:phone", "123-456-7890")

        # Act
        result = self.db.scan_by_prefix("user:1", "contact:")

        # Assert
        expected = "contact:email(alice@example.com), contact:phone(123-456-7890)"
        self.assertEqual(result, expected, "SCAN_BY_PREFIX should only return matching records.")

    @timeout(0.4)
    def test_level2_scan_empty_or_non_existent(self):
        """Tests that SCAN returns an empty string for a non-existent key or a key with no fields."""
        # Arrange
        self.db.set("user:1", "name", "Alice")
        self.db.delete("user:1", "name")
        
        # Act & Assert
        self.assertEqual(self.db.scan("user:1"), "", "SCAN on a key with no fields should be empty.")
        self.assertEqual(self.db.scan("non-existent-key"), "", "SCAN on a non-existent key should be empty.")

    # --------------------------------------------------------------------------
    # Level 3 Tests: Time-Based Operations (TTL)
    # --------------------------------------------------------------------------

    @timeout(0.4)
    def test_level3_get_at_with_ttl(self):
        """Tests that a record with TTL is accessible before expiry but not at or after."""
        # Arrange
        # Record created at timestamp 100, with a TTL of 50. Expires at timestamp 150.
        self.db.set_at_with_ttl("cache:1", "data", "important", 100, 50)
        
        # Act & Assert
        self.assertEqual(self.db.get_at("cache:1", "data", 149), "important", "Should be accessible just before expiry.")
        self.assertEqual(self.db.get_at("cache:1", "data", 150), "", "Should be expired at the exact expiry timestamp.")
        self.assertEqual(self.db.get_at("cache:1", "data", 151), "", "Should be expired after the expiry timestamp.")

    @timeout(0.4)
    def test_level3_delete_at_before_and_after_expiry(self):
        """Tests that a record can be deleted before it expires, but not after."""
        # Arrange
        self.db.set_at_with_ttl("cache:2", "data", "value", 200, 100) # Expires at t=300

        # Act & Assert
        self.assertEqual(self.db.delete_at("cache:2", "data", 250), "true", "Should be able to delete a non-expired record.")
        
        # Re-create for the second part of the test
        self.db.set_at_with_ttl("cache:2", "data", "value", 200, 100) # Expires at t=300
        self.assertEqual(self.db.delete_at("cache:2", "data", 300), "false", "Should not be able to delete an already-expired record.")

    @timeout(0.4)
    def test_level3_scan_at_filters_expired_records(self):
        """Tests that SCAN_AT correctly filters out records that are expired at the given timestamp."""
        # Arrange
        self.db.set_at("perm:1", "config", "stable", 50) # Permanent record
        self.db.set_at_with_ttl("cache:3", "session", "active", 100, 20) # Expires at t=120
        
        # Act & Assert
        # At t=119, both records should exist. We scan both keys to test them together.
        # Note: This assumes your implementation can handle multiple keys. If not, test separately.
        # Let's assume we set them under the same key for a simpler test.
        self.db.set("data", "perm_config", "stable") # Using backward compatible SET
        self.db.set_at_with_ttl("data", "temp_session", "active", 100, 20) # Expires at t=120

        result_before = self.db.scan_at("data", 119)
        self.assertEqual(result_before, "perm_config(stable), temp_session(active)")

        result_after = self.db.scan_at("data", 120)
        self.assertEqual(result_after, "perm_config(stable)", "Expired record should be filtered out.")

    @timeout(0.4)
    def test_level3_scan_by_prefix_at_filters_expired(self):
        """Tests SCAN_BY_PREFIX_AT with expiring records."""
        # Arrange
        self.db.set_at_with_ttl("metrics", "req:success", "100", 100, 50) # Expires at 150
        self.db.set_at_with_ttl("metrics", "req:failure", "5", 100, 50)   # Expires at 150
        self.db.set_at("metrics", "info:version", "v2", 100)

        # Act & Assert
        result_before = self.db.scan_by_prefix_at("metrics", "req:", 149)
        self.assertEqual(result_before, "req:failure(5), req:success(100)")

        result_after = self.db.scan_by_prefix_at("metrics", "req:", 150)
        self.assertEqual(result_after, "", "All matching records are expired, should return empty.")

    @timeout(0.4)
    def test_level3_backward_compatibility(self):
        """Tests that Level 1 commands behave as if timestamp is 0."""
        # Arrange
        self.db.set("compat", "field", "value")
        
        # Act & Assert
        # GET_AT with a future timestamp should still work, as the record has infinite TTL
        self.assertEqual(self.db.get_at("compat", "field", 1000), "value")
        
        # Set a record that expires at t=50
        self.db.set_at_with_ttl("compat", "expiring", "data", 0, 50)
        
        # A simple GET (at t=0) should find it
        self.assertEqual(self.db.get("compat", "expiring"), "data")
        
        # A GET_AT after expiry should not
        self.assertEqual(self.db.get_at("compat", "expiring", 50), "")
