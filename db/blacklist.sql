--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 17.0

-- Started on 2024-11-23 11:13:55 +07

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 16771)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO seal;

--
-- TOC entry 219 (class 1259 OID 16827)
-- Name: url_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.url_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.url_id_seq OWNER TO seal;

--
-- TOC entry 217 (class 1259 OID 16537)
-- Name: url; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.url (
    id integer DEFAULT nextval('public.url_id_seq'::regclass) NOT NULL,
    url text NOT NULL,
    category character varying(100) NOT NULL,
    date_added date NOT NULL,
    reason character varying(500) NOT NULL,
    status boolean,
    source character varying(500) NOT NULL
);


ALTER TABLE public.url OWNER TO seal;

--
-- TOC entry 3456 (class 2606 OID 16775)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3451 (class 2606 OID 16777)
-- Name: url idx_16537_url_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.url
    ADD CONSTRAINT idx_16537_url_pkey PRIMARY KEY (id);


--
-- TOC entry 3454 (class 2606 OID 16991)
-- Name: url url_url_key; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.url
    ADD CONSTRAINT url_url_key UNIQUE (url);


--
-- TOC entry 3452 (class 1259 OID 16814)
-- Name: ix_url_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_url_id ON public.url USING btree (id);


-- Completed on 2024-11-23 11:13:55 +07

--
-- PostgreSQL database dump complete
--

