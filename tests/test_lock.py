import threading
import time
from unittest.mock import patch

import psycopg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from pg_advisory_lock import PgAdvisoryLock, PgAdvisoryLockError, PgAdvisoryLockNotAcquired, PgAdvisoryLockTimeout


def test_lock_defaults():
    lock = PgAdvisoryLock(lock_args=['test'])
    assert lock.raise_on_failure is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_success_on_first_try(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock_immediate', 1], raise_on_failure=raise_on_failure)
    assert lock.lock_immediate(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_success_on_reentry(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock_immediate', 1], raise_on_failure=raise_on_failure)
    with db_session.begin():
        assert lock.lock_immediate(session=db_session) is True
        assert lock.lock_immediate(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_on_first_try(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock', 1], raise_on_failure=raise_on_failure)
    assert lock.lock(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_on_reentry(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'lock', 1], raise_on_failure=raise_on_failure)
    with db_session.begin():
        assert lock.lock(session=db_session) is True
        assert lock.lock(session=db_session) is True


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
def test_lock_immediate_success_after_transaction_ends(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'success_after_commit', 1], raise_on_failure=raise_on_failure)

    with db_session.begin():
        # First transaction acquires and releases lock
        assert lock.lock_immediate(session=db_session) is True

    # Lock is released when the first transaction ends

    with db_session.begin():
        # Second transaction should now be able to acquire the lock
        assert lock.lock_immediate(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_after_transaction_ends(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'success_after_commit'], raise_on_failure=raise_on_failure)
    # First transaction acquires and releases lock
    with db_session.begin():
        assert lock.lock(session=db_session) is True
    # Lock is released when transaction ends

    # Second transaction should be able to acquire the lock
    with db_session.begin():
        assert lock.lock(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_immediate_with_different_keys_succeeds(raise_on_failure, db_session):
    lock1 = PgAdvisoryLock(lock_args=['test_lock', 'key1'], raise_on_failure=raise_on_failure)
    lock2 = PgAdvisoryLock(lock_args=['test_lock', 'key2'], raise_on_failure=raise_on_failure)
    assert lock1.lock_immediate(session=db_session) is True
    assert lock2.lock_immediate(session=db_session) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_with_different_keys_succeeds(raise_on_failure, db_session):
    lock1 = PgAdvisoryLock(lock_args=['test_lock', 'key1'], raise_on_failure=raise_on_failure)
    lock2 = PgAdvisoryLock(lock_args=['test_lock', 'key2'], raise_on_failure=raise_on_failure)
    assert lock1.lock(session=db_session) is True
    assert lock2.lock(session=db_session) is True


@pytest.mark.parametrize(argnames='timeout_value', argvalues=[-1, '1000'])
def test_lock_timeout_validation(timeout_value, db_session):
    lock = PgAdvisoryLock(['test_lock', 'validation'])

    # Test negative timeout raises ValueError
    with pytest.raises(PgAdvisoryLockError, match='Lock timeout must be a non-negative integer.'):
        lock.lock(session=db_session, timeout_in_ms=timeout_value)


def test_lock_zero_timeout_calls_lock_immediate(db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'zero_timeout'])

    # Mock lock_immediate to verify it's called
    with patch.object(lock, 'lock_immediate', return_value=True) as mock_lock_immediate:
        assert lock.lock(session=db_session, timeout_in_ms=0) is True
        mock_lock_immediate.assert_called_once()


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_with_timeout(raise_on_failure, db_session):
    lock = PgAdvisoryLock(lock_args=['test_lock', 'success_with_timeout'], raise_on_failure=raise_on_failure)
    assert lock.lock(session=db_session, timeout_in_ms=500) is True


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(True, False))
def test_lock_success_with_default_timeout(raise_on_failure, db_session):
    locker = PgAdvisoryLock(lock_args=['test_lock', 'default_timeout'], raise_on_failure=raise_on_failure)
    # Test default timeout (1000ms)
    assert locker.lock(session=db_session) is True


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
            started_at = time.monotonic()
            assert lock2.lock(session=session2, timeout_in_ms=100) is False
            elapsed = time.monotonic() - started_at
            # Verify it actually waited (with some tolerance for test execution time)
            assert elapsed >= 0.05


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_propagates_exception(raise_on_failure, db_session):
    lock = PgAdvisoryLock(['test_lock', 'timeout_exception'], raise_on_failure=raise_on_failure)
    error = OperationalError(statement='SELECT 1', params={}, orig=psycopg.errors.ConnectionFailure())

    with patch('pg_advisory_lock.lock.set_lock_timeout', side_effect=error), pytest.raises(OperationalError):
        lock.lock(session=db_session, timeout_in_ms=1000)


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_handles_timeout_exception(raise_on_failure, db_session):
    lock = PgAdvisoryLock(['test_lock', 'timeout_exception'], raise_on_failure=raise_on_failure)
    error = OperationalError(statement='SELECT 1', params={}, orig=psycopg.errors.LockNotAvailable())
    with patch('pg_advisory_lock.lock.set_lock_timeout', side_effect=error):
        if raise_on_failure:
            with pytest.raises(PgAdvisoryLockTimeout):
                lock.lock(session=db_session, timeout_in_ms=1000)
        else:
            assert lock.lock(session=db_session, timeout_in_ms=1000) is False


@pytest.mark.parametrize(argnames='raise_on_failure', argvalues=(False, True))
def test_lock_waits_for_first_transaction_then_succeeds(raise_on_failure, session_factory):
    """Verify a blocked contender acquires the advisory lock after the holder commits.

    Two threads use separate sessions and transactions. The holder acquires the lock
    immediately, while PostgreSQL's `pg_blocking_pids()` confirms that the contender is
    waiting for that holder. The holder then commits, releasing the lock so the contender
    can acquire it before its timeout. Thread completion and errors are asserted explicitly.
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
    }

    def first_transaction():
        """Thread 1: Get lock → wait for thread 2 to start trying → release lock"""
        try:
            with session_factory() as session, session.begin():
                # Get the database backend PID for this transaction.
                holder_pid = session.execute(text('SELECT pg_backend_pid();')).scalar_one()
                lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=raise_on_failure)
                result = lock.lock_immediate(session=session)
                results['first_acquired'] = result

                # 🚦 SIGNAL: "I got the lock!"
                events['first_acquired'].set()

                # 🚦 WAIT: "Don't release until thread 2 starts trying"
                # This ensures thread 2 will definitely be blocked waiting
                assert events['second_started'].wait(timeout=5.0)

                # Check if second transaction has been really blocked
                contender_pid = results['contender_pid']
                deadline = time.monotonic() + 5

                while time.monotonic() < deadline:
                    blocker_pids = session.execute(
                        statement=text('SELECT pg_blocking_pids(:contender_pid)'),
                        params={'contender_pid': contender_pid},
                    ).scalar_one()
                    if holder_pid in blocker_pids:
                        results['contender_was_blocked'] = True
                        break
                    time.sleep(0.01)
                else:
                    raise AssertionError('Contender did not become blocked.')
        except Exception as e:
            results['first_error'] = e

    def second_transaction():
        """Thread 2: Wait for thread 1 to get lock → try to get same lock → should block then succeed"""

        try:
            with session_factory() as session, session.begin():
                # Get the database backend PID for this transaction.
                contender_pid = session.execute(text('SELECT pg_backend_pid();')).scalar_one()
                results['contender_pid'] = contender_pid

                # 🚦 WAIT: "Don't start until thread 1 has the lock"
                # This ensures we're definitely trying to get a lock that's already held
                assert events['first_acquired'].wait(timeout=5.0)

                lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=raise_on_failure)

                # 🚦 SIGNAL: "I'm about to try getting the lock!"
                # This tells thread 1 it's safe to release now
                events['second_started'].set()

                # THIS IS THE KEY PART: This should BLOCK waiting for thread 1 to release,
                # then succeed when thread 1's transaction ends
                result = lock.lock(session=session, timeout_in_ms=10_000)  # 10 second timeout
                results['second_acquired'] = result
        except Exception as e:
            results['second_error'] = e

    # Start both transactions
    thread1 = threading.Thread(target=first_transaction)
    thread2 = threading.Thread(target=second_transaction)

    thread1.start()
    thread2.start()

    # Wait for completion
    thread1.join(timeout=15.0)
    thread2.join(timeout=15.0)

    assert not thread1.is_alive()
    assert not thread2.is_alive()

    # Verify no errors
    assert 'first_error' not in results, f'First transaction error: {results.get("first_error")}'
    assert 'second_error' not in results, f'Second transaction error: {results.get("second_error")}'

    # Verify successful lock acquisition
    assert results.get('first_acquired') is True, 'First transaction should acquire lock immediately'
    assert results.get('second_acquired') is True, 'Second transaction should eventually acquire lock'

    # Second transaction was really blocked
    assert results.get('contender_was_blocked') is True


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


def test_lock_immediate_released_after_rollback(session_factory):
    with session_factory() as holder_session, session_factory() as contender_session:
        lock_args = ('release', 'rollback', 'lock', 'immediate')
        holder_lock = PgAdvisoryLock(lock_args=lock_args)
        contender_lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=False)

        holder_session.begin()

        assert holder_lock.lock_immediate(session=holder_session) is True
        assert contender_lock.lock_immediate(session=contender_session) is False

        holder_session.rollback()

        assert contender_lock.lock_immediate(session=contender_session) is True


def test_lock_released_after_rollback(session_factory):
    with session_factory() as holder_session, session_factory() as contender_session:
        lock_args = ('release', 'rollback', 'lock', 'blocking')
        holder_lock = PgAdvisoryLock(lock_args=lock_args)
        contender_lock = PgAdvisoryLock(lock_args=lock_args, raise_on_failure=False)

        holder_session.begin()

        assert holder_lock.lock(session=holder_session) is True
        assert contender_lock.lock(session=contender_session, timeout_in_ms=100) is False

        holder_session.rollback()
        assert contender_lock.lock(session=contender_session, timeout_in_ms=100) is True
