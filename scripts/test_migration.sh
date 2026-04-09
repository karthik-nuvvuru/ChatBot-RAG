#!/bin/bash
# Test script for conversation schema migration
# Usage: ./scripts/test_migration.sh

set -e

echo "=========================================="
echo "Conversation Schema Migration Test"
echo "=========================================="

# Configuration
ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-alembic.ini}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-chatbot}"
DB_USER="${DB_USER:-postgres}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're running in Docker or locally
check_environment() {
    log_info "Checking environment..."

    if command -v docker &> /dev/null; then
        DOCKER_AVAILABLE=true
    else
        DOCKER_AVAILABLE=false
    fi

    if command -v poetry &> /dev/null; then
        POETRY_AVAILABLE=true
    else
        POETRY_AVAILABLE=false
    fi

    log_info "Docker available: $DOCKER_AVAILABLE"
    log_info "Poetry available: $POETRY_AVAILABLE"
}

# Run migration
run_migration() {
    log_info "Running Alembic migration..."

    if [ "$POETRY_AVAILABLE" = true ]; then
        poetry run alembic upgrade head
    else
        alembic upgrade head
    fi

    log_info "Migration completed successfully"
}

# Verify tables exist
verify_tables() {
    log_info "Verifying tables exist..."

    TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT tablename FROM pg_tables
        WHERE schemaname='public'
        AND tablename LIKE 'conversation_%';
    " 2>/dev/null | tr -d ' ' || echo "")

    EXPECTED_TABLES="conversation_sessions
conversation_messages
conversation_actions
conversation_memory"

    for table in $EXPECTED_TABLES; do
        if echo "$TABLES" | grep -q "^$table$"; then
            log_info "  ✓ $table exists"
        else
            log_error "  ✗ $table NOT FOUND"
            exit 1
        fi
    done
}

# Verify indexes exist
verify_indexes() {
    log_info "Verifying indexes exist..."

    INDEXES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT indexname FROM pg_indexes
        WHERE schemaname='public'
        AND indexname LIKE 'idx_%';
    " 2>/dev/null | tr -d ' ' || echo "")

    EXPECTED_INDEXES="idx_conv_sessions_user_id_active
idx_conv_messages_session_created
idx_conv_memory_embedding"

    for idx in $EXPECTED_INDEXES; do
        if echo "$INDEXES" | grep -q "^$idx$"; then
            log_info "  ✓ $idx exists"
        else
            log_warn "  - $idx not found (may be optional)"
        fi
    done
}

# Verify enum types exist
verify_enums() {
    log_info "Verifying enum types exist..."

    ENUMS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT typname FROM pg_type WHERE typtype = 'e';
    " 2>/dev/null | tr -d ' ' || echo "")

    EXPECTED_ENUMS="session_status
accelerator_type
message_role
action_type
action_status
memory_type"

    for enum in $EXPECTED_ENUMS; do
        if echo "$ENUMS" | grep -q "^$enum$"; then
            log_info "  ✓ $enum enum exists"
        else
            log_error "  ✗ $enum NOT FOUND"
            exit 1
        fi
    done
}

# Test rollback
test_rollback() {
    log_info "Testing rollback..."

    if [ "$POETRY_AVAILABLE" = true ]; then
        poetry run alembic downgrade -1
        log_info "  Rollback successful"

        log_info "Re-applying migration..."
        poetry run alembic upgrade head
    else
        alembic downgrade -1
        log_info "  Rollback successful"

        log_info "Re-applying migration..."
        alembic upgrade head
    fi

    log_info "Migration re-applied successfully"
}

# Run performance test (basic)
run_perf_test() {
    log_info "Running basic performance test..."

    START_TIME=$(date +%s%N)

    # Insert test session
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        INSERT INTO conversation_sessions (user_id, engagement_id, project_id, accelerator_type)
        VALUES ('test-user', NULL, NULL, 'basic')
        RETURNING session_id;
    " > /dev/null 2>&1

    END_TIME=$(date +%s%N)
    DURATION=$(( (END_TIME - START_TIME) / 1000000 ))

    log_info "  Single insert took: ${DURATION}ms"

    if [ "$DURATION" -gt 100 ]; then
        log_warn "  Insert is slower than expected (>100ms)"
    else
        log_info "  Insert performance: OK"
    fi
}

# Cleanup test data
cleanup() {
    log_info "Cleaning up test data..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        DELETE FROM conversation_sessions WHERE user_id = 'test-user';
    " > /dev/null 2>&1

    log_info "Cleanup completed"
}

# Main
main() {
    check_environment

    echo ""
    log_info "Starting migration test..."
    echo ""

    run_migration
    echo ""

    verify_tables
    echo ""

    verify_indexes
    echo ""

    verify_enums
    echo ""

    run_perf_test
    echo ""

    cleanup
    echo ""

    echo "=========================================="
    log_info "All tests passed!"
    echo "=========================================="
}

main "$@"
