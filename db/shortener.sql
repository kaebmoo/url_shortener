--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 17.0

-- Started on 2024-11-23 11:15:56 +07

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
-- SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 863 (class 1247 OID 16840)
-- Name: status_enum; Type: TYPE; Schema: public; Owner: seal
--

CREATE TYPE public.status_enum AS ENUM (
    '0',
    'Dangerous',
    'Safe',
    'In queue for scanning',
    '-1',
    '1',
    'No conclusive information',
    'No classification'
);


ALTER TYPE public.status_enum OWNER TO seal;

--
-- TOC entry 224 (class 1255 OID 16859)
-- Name: insert_url_to_check(); Type: FUNCTION; Schema: public; Owner: seal
--

CREATE FUNCTION public.insert_url_to_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO urls_to_check (url) VALUES (NEW.target_url);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.insert_url_to_check() OWNER TO seal;

--
-- TOC entry 225 (class 1255 OID 17084)
-- Name: notify_new_url(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.notify_new_url() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_notify('new_url', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.notify_new_url() OWNER TO postgres;

--
-- TOC entry 226 (class 1255 OID 17086)
-- Name: notify_url_change(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.notify_url_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_notify('url_change', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.notify_url_change() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 16462)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.alembic_version (
    version_num text NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO seal;

--
-- TOC entry 222 (class 1259 OID 16823)
-- Name: scan_records_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.scan_records_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scan_records_id_seq OWNER TO seal;

--
-- TOC entry 220 (class 1259 OID 16472)
-- Name: scan_records; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.scan_records (
    id integer DEFAULT nextval('public.scan_records_id_seq'::regclass) NOT NULL,
    "timestamp" timestamp with time zone,
    url character varying,
    status character varying,
    scan_type character varying,
    result character varying,
    submission_type character varying,
    scan_id character varying,
    sha256 character varying
);


ALTER TABLE public.scan_records OWNER TO seal;

--
-- TOC entry 221 (class 1259 OID 16821)
-- Name: urls_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.urls_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urls_id_seq OWNER TO seal;

--
-- TOC entry 217 (class 1259 OID 16455)
-- Name: urls; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.urls (
    id integer DEFAULT nextval('public.urls_id_seq'::regclass) NOT NULL,
    key character varying,
    secret_key character varying,
    target_url character varying,
    is_active boolean,
    clicks integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone,
    api_key character varying,
    is_checked boolean DEFAULT false,
    status character varying,
    title character varying(255),
    favicon_url character varying(255)
);


ALTER TABLE public.urls OWNER TO seal;

--
-- TOC entry 223 (class 1259 OID 16825)
-- Name: urls_to_check_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.urls_to_check_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urls_to_check_id_seq OWNER TO seal;

--
-- TOC entry 219 (class 1259 OID 16467)
-- Name: urls_to_check; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.urls_to_check (
    id integer DEFAULT nextval('public.urls_to_check_id_seq'::regclass) NOT NULL,
    url character varying
);


ALTER TABLE public.urls_to_check OWNER TO seal;

--
-- TOC entry 3471 (class 2606 OID 16644)
-- Name: urls idx_16455_urls_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT idx_16455_urls_pkey PRIMARY KEY (id);


--
-- TOC entry 3478 (class 2606 OID 16497)
-- Name: alembic_version idx_16462_sqlite_autoindex_alembic_version_1; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT idx_16462_sqlite_autoindex_alembic_version_1 PRIMARY KEY (version_num);


--
-- TOC entry 3480 (class 2606 OID 16695)
-- Name: urls_to_check idx_16467_urls_to_check_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.urls_to_check
    ADD CONSTRAINT idx_16467_urls_to_check_pkey PRIMARY KEY (id);


--
-- TOC entry 3483 (class 2606 OID 16635)
-- Name: scan_records idx_16472_scan_records_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.scan_records
    ADD CONSTRAINT idx_16472_scan_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3484 (class 1259 OID 16642)
-- Name: ix_scan_records_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_scan_records_id ON public.scan_records USING btree (id);


--
-- TOC entry 3472 (class 1259 OID 16689)
-- Name: ix_urls_api_key; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_urls_api_key ON public.urls USING btree (api_key);


--
-- TOC entry 3473 (class 1259 OID 16690)
-- Name: ix_urls_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_urls_id ON public.urls USING btree (id);


--
-- TOC entry 3474 (class 1259 OID 16691)
-- Name: ix_urls_key; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX ix_urls_key ON public.urls USING btree (key);


--
-- TOC entry 3475 (class 1259 OID 16692)
-- Name: ix_urls_secret_key; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX ix_urls_secret_key ON public.urls USING btree (secret_key);


--
-- TOC entry 3476 (class 1259 OID 16693)
-- Name: ix_urls_target_url; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_urls_target_url ON public.urls USING btree (target_url);


--
-- TOC entry 3481 (class 1259 OID 16702)
-- Name: ix_urls_to_check_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_urls_to_check_id ON public.urls_to_check USING btree (id);


--
-- TOC entry 3485 (class 2620 OID 16860)
-- Name: urls check_new_url; Type: TRIGGER; Schema: public; Owner: seal
--

CREATE TRIGGER check_new_url AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.insert_url_to_check();


--
-- TOC entry 3486 (class 2620 OID 17085)
-- Name: urls new_url_trigger; Type: TRIGGER; Schema: public; Owner: seal
--

CREATE TRIGGER new_url_trigger AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_new_url();


--
-- TOC entry 3487 (class 2620 OID 17087)
-- Name: urls url_insert_trigger; Type: TRIGGER; Schema: public; Owner: seal
--

CREATE TRIGGER url_insert_trigger AFTER INSERT ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_url_change();


--
-- TOC entry 3488 (class 2620 OID 17088)
-- Name: urls url_update_trigger; Type: TRIGGER; Schema: public; Owner: seal
--

CREATE TRIGGER url_update_trigger AFTER UPDATE ON public.urls FOR EACH ROW EXECUTE FUNCTION public.notify_url_change();


-- Completed on 2024-11-23 11:15:56 +07

--
-- PostgreSQL database dump complete
--

