-- Migration V024: Create Refresh Function for Supply Chain Traceability
-- 
-- Creates the missing refresh function that the DeterministicTransparencyService expects.
-- This function refreshes the supply_chain_traceability materialized view.

-- Create the refresh function
CREATE OR REPLACE FUNCTION refresh_supply_chain_traceability()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Refresh the materialized view
    REFRESH MATERIALIZED VIEW supply_chain_traceability;
    
    -- Log the refresh event
    INSERT INTO system_events (event_type, event_data) 
    VALUES (
        'materialized_view_refresh', 
        jsonb_build_object(
            'view_name', 'supply_chain_traceability',
            'refreshed_at', CURRENT_TIMESTAMP,
            'triggered_by', 'refresh_supply_chain_traceability()'
        )
    );
END;
$$;

-- Add comment explaining the function
COMMENT ON FUNCTION refresh_supply_chain_traceability() IS
'Refreshes the supply_chain_traceability materialized view and logs the event.
Called by DeterministicTransparencyService to ensure real-time transparency calculations.';

-- Test the function
SELECT refresh_supply_chain_traceability();

-- Log the migration
INSERT INTO system_events (event_type, event_data) 
VALUES (
    'schema_migration', 
    jsonb_build_object(
        'migration', 'V024__create_refresh_function',
        'description', 'Created refresh function for supply_chain_traceability materialized view',
        'function_created', 'refresh_supply_chain_traceability()',
        'purpose', 'Enable real-time transparency calculations in DeterministicTransparencyService'
    )
);
