# Database Schema Fix Instructions

## Problem
The application is failing with the error:
```
(psycopg2.errors.UndefinedColumn) column gift_cards.currency does not exist
```

This happens because the database schema is out of sync with the model definitions.

## Solution

### Option 1: Using Flask-Migrate (Recommended)

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Flask-Migrate** (if not already done):
   ```bash
   flask db init
   ```

3. **Create a migration** for the missing currency column:
   ```bash
   flask db migrate -m "Add currency column to gift_cards"
   ```

4. **Apply the migration**:
   ```bash
   flask db upgrade
   ```

### Option 2: Direct SQL Fix

If Flask-Migrate is not set up, you can run this SQL directly on your PostgreSQL database:

```sql
-- Check if the currency column exists, if not add it
DO $$
BEGIN
    -- Check if the currency column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'gift_cards' 
        AND column_name = 'currency'
    ) THEN
        -- Add the currency column
        ALTER TABLE gift_cards ADD COLUMN currency VARCHAR(20) DEFAULT 'Robux';
        
        -- Update existing records to have the default currency
        UPDATE gift_cards SET currency = 'Robux' WHERE currency IS NULL;
        
        RAISE NOTICE 'Currency column added to gift_cards table';
    ELSE
        RAISE NOTICE 'Currency column already exists in gift_cards table';
    END IF;
END $$;
```

### Option 3: Using the Fix Script

Run the provided fix script when the database is accessible:

```bash
python3 fix_database_schema.py
```

## Verification

After applying the fix, verify it works by running:

```bash
flask db init
```

This should now work without the currency column error.

## Additional Notes

- The `currency` column was added to the `GiftCard` model but the database table wasn't updated
- This is a common issue when model changes aren't properly migrated to the database
- Flask-Migrate should be used for all future schema changes to prevent this issue