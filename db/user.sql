--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 17.0

-- Started on 2024-11-23 11:17:08 +07

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
-- TOC entry 220 (class 1259 OID 16424)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.alembic_version (
    version_num text NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO seal;

--
-- TOC entry 223 (class 1259 OID 16837)
-- Name: editable_html_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.editable_html_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.editable_html_id_seq OWNER TO seal;

--
-- TOC entry 218 (class 1259 OID 16413)
-- Name: editable_html; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.editable_html (
    id bigint DEFAULT nextval('public.editable_html_id_seq'::regclass) NOT NULL,
    editor_name text,
    value text
);


ALTER TABLE public.editable_html OWNER TO seal;

--
-- TOC entry 222 (class 1259 OID 16835)
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO seal;

--
-- TOC entry 217 (class 1259 OID 16408)
-- Name: roles; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.roles (
    id bigint DEFAULT nextval('public.roles_id_seq'::regclass) NOT NULL,
    name text,
    index text,
    "default" boolean,
    permissions bigint
);


ALTER TABLE public.roles OWNER TO seal;

--
-- TOC entry 221 (class 1259 OID 16833)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO seal;

--
-- TOC entry 219 (class 1259 OID 16418)
-- Name: users; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.users (
    id bigint DEFAULT nextval('public.users_id_seq'::regclass) NOT NULL,
    confirmed boolean,
    first_name text,
    last_name text,
    email text,
    password_hash text,
    role_id bigint,
    phone_number text,
    uid text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO seal;

--
-- TOC entry 3465 (class 2606 OID 16447)
-- Name: roles idx_16408_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT idx_16408_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3468 (class 2606 OID 16446)
-- Name: editable_html idx_16413_editable_html_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.editable_html
    ADD CONSTRAINT idx_16413_editable_html_pkey PRIMARY KEY (id);


--
-- TOC entry 3476 (class 2606 OID 16448)
-- Name: users idx_16418_users_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT idx_16418_users_pkey PRIMARY KEY (id);


--
-- TOC entry 3478 (class 2606 OID 16449)
-- Name: alembic_version idx_16424_sqlite_autoindex_alembic_version_1; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT idx_16424_sqlite_autoindex_alembic_version_1 PRIMARY KEY (version_num);


--
-- TOC entry 3463 (class 1259 OID 16429)
-- Name: idx_16408_ix_roles_default; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX idx_16408_ix_roles_default ON public.roles USING btree ("default");


--
-- TOC entry 3466 (class 1259 OID 16432)
-- Name: idx_16408_sqlite_autoindex_roles_1; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX idx_16408_sqlite_autoindex_roles_1 ON public.roles USING btree (name);


--
-- TOC entry 3469 (class 1259 OID 16431)
-- Name: idx_16413_sqlite_autoindex_editable_html_1; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX idx_16413_sqlite_autoindex_editable_html_1 ON public.editable_html USING btree (editor_name);


--
-- TOC entry 3470 (class 1259 OID 16438)
-- Name: idx_16418_ix_users_email; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX idx_16418_ix_users_email ON public.users USING btree (email);


--
-- TOC entry 3471 (class 1259 OID 16436)
-- Name: idx_16418_ix_users_first_name; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX idx_16418_ix_users_first_name ON public.users USING btree (first_name);


--
-- TOC entry 3472 (class 1259 OID 16440)
-- Name: idx_16418_ix_users_last_name; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX idx_16418_ix_users_last_name ON public.users USING btree (last_name);


--
-- TOC entry 3473 (class 1259 OID 16435)
-- Name: idx_16418_ix_users_phone_number; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX idx_16418_ix_users_phone_number ON public.users USING btree (phone_number);


--
-- TOC entry 3474 (class 1259 OID 16433)
-- Name: idx_16418_ix_users_uid; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX idx_16418_ix_users_uid ON public.users USING btree (uid);


--
-- TOC entry 3479 (class 2606 OID 16450)
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


-- Completed on 2024-11-23 11:17:09 +07

--
-- PostgreSQL database dump complete
--

