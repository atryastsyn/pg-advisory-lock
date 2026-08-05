import threading
import time
from unittest.mock import patch

import psycopg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.pg_advisory_lock import PgAdvisoryLock, PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout


def test_lock_defaults():
    lock = PgAdvisoryLock(lock_args=['test'])
    assert lock.raise_on_failure is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_success_on_first_try(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock_immediate', 1], raise_on_failure=raise_on_failure)
    with session_factory() as session:
        assert lock.lock_immediate(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_on_first_try(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock', 1], raise_on_failure=raise_on_failure)
    with session_factory() as session:
        assert lock.lock(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_fails_when_already_locked(raise_on_failure, session_factory):
    lock_args = ['test_lock', 'concurrent', 1]

    # Create two separate sessions for true concurrency
    with session_factory() as session1, session_factory() as session2:
        # First session acquires the lock
        with session1.begin():
            lock1 = PgAdvisoryLock(lock_args)
            assert lock1.lock_immediate(session=session1) is True

            lock2 = PgAdvisoryLock(lock_args, raise_on_failure=raise_on_failure)
            if raise_on_failure:
                with pytest.raises(PgAdvisoryLockNotAcquired):
                    lock2.lock_immediate(session=session2)
            else:
                assert lock2.lock_immediate(session=session2) is False

        # Now second session should be able to acquire it
        assert lock2.lock_immediate(session=session2) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_success_after_transaction_ends(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'success_after_commit', 1], raise_on_failure=raise_on_failure)

    with session_factory() as session:
        with session.begin():
            # First transaction acquires and releases lock
            assert lock.lock_immediate(session=session) is True

        # Lock is released when the first transaction ends

        with session.begin():
            # Second transaction should now be able to acquire the lock
            assert lock.lock_immediate(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_after_transaction_ends(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'success_after_commit'], raise_on_failure=raise_on_failure)
    # First transaction acquires and releases lock
    with session_factory() as session:
        with session.begin():
            assert lock.lock(session=session) is True
        # Lock is released when transaction ends

        # Second transaction should be able to acquire the lock
        with session.begin():
            assert lock.lock(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_with_different_keys_succeeds(raise_on_failure, session_factory):
    with session_factory() as session, session.begin():
        lock1 = PgAdvisoryLock(lock_args=['test_lock', 'key1'], raise_on_failure=raise_on_failure)
        lock2 = PgAdvisoryLock(lock_args=['test_lock', 'key2'], raise_on_failure=raise_on_failure)
        assert lock1.lock_immediate(session=session) is True
        assert lock2.lock_immediate(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_with_different_keys_succeeds(raise_on_failure, session_factory):
    with session_factory() as session, session.begin():
        lock1 = PgAdvisoryLock(lock_args=['test_lock', 'key1'], raise_on_failure=raise_on_failure)
        lock2 = PgAdvisoryLock(lock_args=['test_lock', 'key2'], raise_on_failure=raise_on_failure)
        assert lock1.lock(session=session) is True
        assert lock2.lock(session=session) is True


@pytest.mark.parametrize(argnames='timeout_value', argvalues=[-1, '1000'])
def test_lock_timeout_validation(timeout_value, session_factory):
    lock = PgAdvisoryLock(['test_lock', 'validation'])

    # Test negative timeout raises ValueError
    with (
        session_factory() as session,
        pytest.raises(PgAdvisoryLockError, match='Lock timeout must be a non-negative integer.'),
    ):
        lock.lock(session=session, timeout_in_ms=timeout_value)


def test_lock_zero_timeout_calls_lock_immediate(session_factory):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'zero_timeout'])

    # Mock lock_immediate to verify it's called
    with session_factory() as session, patch.object(lock, 'lock_immediate', return_value=True) as mock_lock_immediate:
        assert lock.lock(session=session, timeout_in_ms=0) is True
        mock_lock_immediate.assert_called_once()


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_with_timeout(raise_on_failure, session_factory):
    with session_factory() as session, session.begin():
        lock = PgAdvisoryLock(lock_args=['test_lock', 'success_with_timeout'], raise_on_failure=raise_on_failure)
        assert lock.lock(session=session, timeout_in_ms=500) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_with_default_timeout(raise_on_failure, session_factory):
    locker = PgAdvisoryLock(lock_args=['test_lock', 'default_timeout'], raise_on_failure=raise_on_failure)
    # Test default timeout (1000ms)
    with session_factory() as session, session.begin():
        assert locker.lock(session=session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_timeout_when_already_locked(raise_on_failure, session_factory):
    lock_args = ['test_lock', 'timeout_test', 1]

    # Create two separate sessions for true concurrency
    with session_factory() as session1, session_factory() as session2:
        # First session acquires the lock
        lock1 = PgAdvisoryLock(lock_args)
        assert lock1.lock(session=session1, timeout_in_ms=100) is True

        # Second session behavior depends on raise_on_failure parameter
        lock2 = PgAdvisoryLock(lock_args, raise_on_failure=raise_on_failure)

        if raise_on_failure:  # Should raise exception
            with pytest.raises(PgAdvisoryLockTimeout):
                lock2.lock(session=session2, timeout_in_ms=100)

        else:  # Should return False and measure timing
            start_time = time.time()
            assert lock2.lock(session=session2, timeout_in_ms=100) is False
            end_time = time.time()
            # Verify it actually waited (with some tolerance for test execution time)
            assert 0.08 <= (end_time - start_time) <= 0.3


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_propagates_exception(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(['test_lock', 'timeout_exception'], raise_on_failure=raise_on_failure)
    error = OperationalError(statement='SELECT 1', params={}, orig=psycopg.errors.ConnectionFailure())

    with (
        session_factory() as session,
        patch('src.pg_advisory_lock.lock.set_lock_timeout', side_effect=error),
        pytest.raises(OperationalError),
    ):
        lock.lock(session=session, timeout_in_ms=1000)


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_handles_timeout_exception(raise_on_failure, session_factory):
    lock = PgAdvisoryLock(['test_lock', 'timeout_exception'], raise_on_failure=raise_on_failure)
    error = OperationalError(statement='SELECT 1', params={}, orig=psycopg.errors.LockNotAvailable())
    with session_factory() as session, patch('src.pg_advisory_lock.lock.set_lock_timeout', side_effect=error):
        if raise_on_failure:
            with pytest.raises(PgAdvisoryLockTimeout):
                lock.lock(session=session, timeout_in_ms=1000)
        else:
            assert lock.lock(session=session, timeout_in_ms=1000) is False


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_waits_for_first_transaction_then_succeeds(raise_on_failure, session_factory):
    """
    Test PostgreSQL advisory lock blocking behavior with timeout in concurrent transactions.

    This test verifies the core functionality of PGAdvisoryLocker.lock() method when dealing
    with lock contention between multiple database transactions. It ensures that:

    1. First transaction can acquire an advisory lock immediately
    2. Second transaction blocks when trying to acquire the same lock (doesn't fail immediately)
    3. Second transaction successfully acquires the lock after first transaction commits
    4. The whole process completes within the specified timeout period

    Scenario:
    - Thread 1: Gets advisory lock, holds it for ~100ms, then releases by committing transaction
    - Thread 2: Waits for Thread 1 to acquire lock, then calls lock(timeout_in_ms=2000)
                This should block (not return immediately) until Thread 1 releases the lock

    This simulates real-world scenarios like:
    - Payment processing where only one transaction should process a specific order
    - User data synchronization where concurrent updates must be serialized
    - Scheduled job execution where duplicate runs must be prevented

    The test proves that PostgreSQL advisory locks work as distributed mutexes across
    separate database connections/transactions, with proper timeout handling.
    """
    lock_args = ['test_lock', 'concurrent_wait_success', 123]

    # Shared state between threads
    results = {}

    # These are like traffic lights between the threads:
    events = {
        # Green light: "First thread has acquired the lock"
        'first_acquired': threading.Event(),
        # Green light: "Second thread is now trying to get the lock"
        'second_started': threading.Event(),
        # Green light: "First thread can now release the lock"
        'first_can_release': threading.Event(),
    }

    def first_transaction():
        """Thread 1: Get lock → wait for thread 2 to start trying → release lock"""
        session = session_factory()
        try:
            lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=raise_on_failure)
            result = lock.lock_immediate(session=session)
            results['first_acquired'] = result
            results['first_acquire_time'] = time.time()

            # 🚦 SIGNAL: "I got the lock!"
            events['first_acquired'].set()

            # 🚦 WAIT: "Don't release until thread 2 starts trying"
            # This ensures thread 2 will definitely be blocked waiting
            events['second_started'].wait(timeout=5.0)

            # Hold lock a bit longer to ensure second transaction waits
            time.sleep(0.1)
            results['first_release_time'] = time.time()
            # Lock released when transaction commits
            events['first_can_release'].set()
        except Exception as e:
            results['first_error'] = e
        finally:
            session.close()

    def second_transaction():
        """Thread 2: Wait for thread 1 to get lock → try to get same lock → should block then succeed"""
        session = session_factory()
        try:
            # 🚦 WAIT: "Don't start until thread 1 has the lock"
            # This ensures we're definitely trying to get a lock that's already held
            events['first_acquired'].wait(timeout=5.0)

            # Small delay to ensure we're definitely trying while first holds lock
            time.sleep(0.05)

            lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=raise_on_failure)
            results['second_start_time'] = time.time()

            # 🚦 SIGNAL: "I'm about to try getting the lock!"
            # This tells thread 1 it's safe to release now
            events['second_started'].set()

            # THIS IS THE KEY PART: This should BLOCK waiting for thread 1 to release,
            # then succeed when thread 1's transaction ends
            result = lock.lock(session=session, timeout_in_ms=2000)  # 2 second timeout
            results['second_acquired'] = result
            results['second_success_time'] = time.time()
        except Exception as e:
            results['second_error'] = e
        finally:
            session.close()

    # Start both transactions
    thread1 = threading.Thread(target=first_transaction)
    thread2 = threading.Thread(target=second_transaction)

    start_time = time.time()
    thread1.start()
    thread2.start()

    # Wait for completion
    thread1.join(timeout=10.0)
    thread2.join(timeout=10.0)
    total_time = time.time() - start_time

    # Verify no errors
    assert 'first_error' not in results, f'First transaction error: {results.get("first_error")}'
    assert 'second_error' not in results, f'Second transaction error: {results.get("second_error")}'

    # Verify successful lock acquisition
    assert results.get('first_acquired') is True, 'First transaction should acquire lock immediately'
    assert results.get('second_acquired') is True, 'Second transaction should eventually acquire lock'

    # Verify timing relationships
    assert 'first_acquire_time' in results
    assert 'first_release_time' in results
    assert 'second_start_time' in results
    assert 'second_success_time' in results

    # Second should start trying after first acquired
    assert results['second_start_time'] >= results['first_acquire_time']

    # Second should succeed after first released (with some tolerance for transaction commit)
    assert results['second_success_time'] >= results['first_release_time'] - 0.1

    # Second transaction should have waited (not succeeded immediately)
    wait_duration = results['second_success_time'] - results['second_start_time']
    assert wait_duration >= 0.1, f'Second transaction should have waited, but only took {wait_duration:.3f}s'
    assert wait_duration <= 1.0, f'Second transaction waited too long: {wait_duration:.3f}s'

    # Total test should complete reasonably quickly
    assert total_time <= 5.0, f'Test took too long: {total_time:.3f}s'


def test_lock_timeout_returning_false_keeps_transaction_usable(session_factory):
    """A handled lock timeout must not abort the caller's transaction."""
    lock_args = ['test_lock', 'transaction_remains_usable', 'boolean']

    with (
        session_factory() as holder_session,
        session_factory() as contender_session,
        holder_session.begin(),
        contender_session.begin(),
    ):
        holder = PgAdvisoryLock(lock_args)
        contender = PgAdvisoryLock(lock_args, raise_on_failure=False)

        assert holder.lock_immediate(session=holder_session) is True
        acquired = contender.lock(session=contender_session, timeout_in_ms=20)
        query_result = contender_session.execute(text('SELECT 1')).scalar_one()

        assert acquired is False
        assert query_result == 1


def test_lock_timeout_exception_keeps_transaction_usable(session_factory):
    """Catching a lock timeout must leave the caller's transaction usable."""
    lock_args = ['test_lock', 'transaction_remains_usable', 'exception']

    with (
        session_factory() as holder_session,
        session_factory() as contender_session,
        holder_session.begin(),
        contender_session.begin(),
    ):
        holder = PgAdvisoryLock(lock_args)
        contender = PgAdvisoryLock(lock_args)

        assert holder.lock_immediate(session=holder_session) is True
        with pytest.raises(PgAdvisoryLockTimeout):
            contender.lock(session=contender_session, timeout_in_ms=20)
        query_result = contender_session.execute(text('SELECT 1')).scalar_one()
        assert query_result == 1
