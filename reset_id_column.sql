DO $$ 
DECLARE
    tbl RECORD;
    seq_name TEXT;
BEGIN
    -- วนลูปตารางทั้งหมดที่มีคอลัมน์ id
    FOR tbl IN SELECT table_name
               FROM information_schema.columns
               WHERE column_name = 'id'
                 AND table_schema = 'public' -- ใช้เฉพาะตารางใน schema 'public'
    LOOP
        -- ดึงชื่อ sequence สำหรับตารางนั้น ๆ
        seq_name := pg_get_serial_sequence(tbl.table_name, 'id');
        
        -- ตรวจสอบว่า sequence มีอยู่จริง
        IF seq_name IS NOT NULL THEN
            -- รีเซ็ตลำดับ sequence โดยใช้ค่า MAX(id)
            EXECUTE format('SELECT setval(''%I'', COALESCE(MAX(id), 1)) FROM %I',
                            seq_name, tbl.table_name);
        END IF;
    END LOOP;
END $$;
