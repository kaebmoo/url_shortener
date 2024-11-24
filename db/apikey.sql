--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 17.0

-- Started on 2024-11-23 11:07:14 +07

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
-- TOC entry 219 (class 1259 OID 16709)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO seal;

--
-- TOC entry 220 (class 1259 OID 16829)
-- Name: apikey_id_seq; Type: SEQUENCE; Schema: public; Owner: seal
--

CREATE SEQUENCE public.apikey_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.apikey_id_seq OWNER TO seal;

--
-- TOC entry 218 (class 1259 OID 16516)
-- Name: api_key; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.api_key (
    id integer DEFAULT nextval('public.apikey_id_seq'::regclass) NOT NULL,
    role_id integer,
    api_key character varying(64)
);


ALTER TABLE public.api_key OWNER TO seal;

--
-- TOC entry 223 (class 1259 OID 17007)
-- Name: api_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.api_user (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    password_hash character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true,
    email_verified boolean DEFAULT false,
    phone_verified boolean DEFAULT false,
    role_id integer,
    api_key_id integer
);


ALTER TABLE public.api_user OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 17006)
-- Name: api_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.api_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_user_id_seq OWNER TO postgres;

--
-- TOC entry 3635 (class 0 OID 0)
-- Dependencies: 222
-- Name: api_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.api_user_id_seq OWNED BY public.api_user.id;


--
-- TOC entry 221 (class 1259 OID 16831)
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
-- TOC entry 217 (class 1259 OID 16511)
-- Name: roles; Type: TABLE; Schema: public; Owner: seal
--

CREATE TABLE public.roles (
    id integer DEFAULT nextval('public.roles_id_seq'::regclass) NOT NULL,
    name character varying(64)
);


ALTER TABLE public.roles OWNER TO seal;

--
-- TOC entry 3461 (class 2604 OID 17010)
-- Name: api_user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user ALTER COLUMN id SET DEFAULT nextval('public.api_user_id_seq'::regclass);


--
-- TOC entry 3477 (class 2606 OID 16713)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3479 (class 2606 OID 17021)
-- Name: api_user api_user_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_email_key UNIQUE (email);


--
-- TOC entry 3481 (class 2606 OID 17023)
-- Name: api_user api_user_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_phone_number_key UNIQUE (phone_number);


--
-- TOC entry 3483 (class 2606 OID 17019)
-- Name: api_user api_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_pkey PRIMARY KEY (id);


--
-- TOC entry 3468 (class 2606 OID 16744)
-- Name: roles idx_16511_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT idx_16511_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3473 (class 2606 OID 16715)
-- Name: api_key idx_16516_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT idx_16516_api_key_pkey PRIMARY KEY (id);


--
-- TOC entry 3471 (class 2606 OID 16765)
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 3474 (class 1259 OID 16741)
-- Name: ix_api_key_api_key; Type: INDEX; Schema: public; Owner: seal
--

CREATE UNIQUE INDEX ix_api_key_api_key ON public.api_key USING btree (api_key);


--
-- TOC entry 3475 (class 1259 OID 16742)
-- Name: ix_api_key_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_api_key_id ON public.api_key USING btree (id);


--
-- TOC entry 3469 (class 1259 OID 16763)
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: seal
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- TOC entry 3484 (class 2606 OID 16745)
-- Name: api_key api_key_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: seal
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- TOC entry 3485 (class 2606 OID 17029)
-- Name: api_user api_user_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.api_key(id);


--
-- TOC entry 3486 (class 2606 OID 17024)
-- Name: api_user api_user_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_user
    ADD CONSTRAINT api_user_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


-- Completed on 2024-11-23 11:07:14 +07

--
-- PostgreSQL database dump complete
--

