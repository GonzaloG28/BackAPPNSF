--
-- PostgreSQL database dump
--

\restrict AHn5U41Qpg90Nuhfksa6kuGdQBzZOaGLoYb9Pfw7WYj0SFsd03Xi8hUbxcuopzf

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: attendanceshift; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attendanceshift AS ENUM (
    'AM',
    'PM',
    'AM_PM',
    'ABSENT'
);


ALTER TYPE public.attendanceshift OWNER TO postgres;

--
-- Name: convocatoriastatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.convocatoriastatus AS ENUM (
    'DRAFT',
    'CONFIRMED',
    'EXPORTED'
);


ALTER TYPE public.convocatoriastatus OWNER TO postgres;

--
-- Name: importstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.importstatus AS ENUM (
    'SUCCESS',
    'PARTIAL',
    'FAILED'
);


ALTER TYPE public.importstatus OWNER TO postgres;

--
-- Name: importtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.importtype AS ENUM (
    'ROSTER',
    'ATTENDANCE',
    'TIMES',
    'QUALIFYING_TIMES'
);


ALTER TYPE public.importtype OWNER TO postgres;

--
-- Name: scheduleshift; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.scheduleshift AS ENUM (
    'AM',
    'PM',
    'AM_PM',
    'NONE'
);


ALTER TYPE public.scheduleshift OWNER TO postgres;

--
-- Name: stroketype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.stroketype AS ENUM (
    'FREE',
    'BACK',
    'BREAST',
    'FLY',
    'MEDLEY'
);


ALTER TYPE public.stroketype OWNER TO postgres;

--
-- Name: swimmergender; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.swimmergender AS ENUM (
    'MALE',
    'FEMALE'
);


ALTER TYPE public.swimmergender OWNER TO postgres;

--
-- Name: swimmerprofile; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.swimmerprofile AS ENUM (
    'COMPETITIVE',
    'FORMATIVE'
);


ALTER TYPE public.swimmerprofile OWNER TO postgres;

--
-- Name: swimmerstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.swimmerstatus AS ENUM (
    'ACTIVE',
    'FROZEN',
    'DELETED'
);


ALTER TYPE public.swimmerstatus OWNER TO postgres;

--
-- Name: timesource; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.timesource AS ENUM (
    'TRAINING',
    'COMPETITION',
    'IMPORT'
);


ALTER TYPE public.timesource OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attendance_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attendance_logs (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    date date NOT NULL,
    complied boolean NOT NULL
);


ALTER TABLE public.attendance_logs OWNER TO postgres;

--
-- Name: attendance_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attendance_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attendance_logs_id_seq OWNER TO postgres;

--
-- Name: attendance_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attendance_logs_id_seq OWNED BY public.attendance_logs.id;


--
-- Name: attendances; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attendances (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    date date NOT NULL,
    session_id integer,
    shift public.attendanceshift DEFAULT 'ABSENT'::public.attendanceshift NOT NULL
);


ALTER TABLE public.attendances OWNER TO postgres;

--
-- Name: attendances_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attendances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attendances_id_seq OWNER TO postgres;

--
-- Name: attendances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attendances_id_seq OWNED BY public.attendances.id;


--
-- Name: competitions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.competitions (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    organizer character varying(150),
    date date NOT NULL,
    location character varying(150),
    max_events_per_swimmer integer DEFAULT 3 NOT NULL
);


ALTER TABLE public.competitions OWNER TO postgres;

--
-- Name: competitions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.competitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.competitions_id_seq OWNER TO postgres;

--
-- Name: competitions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.competitions_id_seq OWNED BY public.competitions.id;


--
-- Name: convocatoria_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.convocatoria_entries (
    id integer NOT NULL,
    convocatoria_id integer NOT NULL,
    swimmer_id integer NOT NULL,
    event_type_id integer NOT NULL,
    qualifying_time_id integer,
    best_time_seconds numeric(10,2),
    selected boolean,
    time_record_date date
);


ALTER TABLE public.convocatoria_entries OWNER TO postgres;

--
-- Name: convocatoria_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.convocatoria_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.convocatoria_entries_id_seq OWNER TO postgres;

--
-- Name: convocatoria_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.convocatoria_entries_id_seq OWNED BY public.convocatoria_entries.id;


--
-- Name: convocatorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.convocatorias (
    id integer NOT NULL,
    competition_id integer NOT NULL,
    created_by integer,
    status public.convocatoriastatus NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.convocatorias OWNER TO postgres;

--
-- Name: convocatorias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.convocatorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.convocatorias_id_seq OWNER TO postgres;

--
-- Name: convocatorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.convocatorias_id_seq OWNED BY public.convocatorias.id;


--
-- Name: event_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    distance_m integer NOT NULL,
    stroke public.stroketype NOT NULL
);


ALTER TABLE public.event_types OWNER TO postgres;

--
-- Name: event_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.event_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.event_types_id_seq OWNER TO postgres;

--
-- Name: event_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.event_types_id_seq OWNED BY public.event_types.id;


--
-- Name: exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exercises (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.exercises OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exercises_id_seq OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exercises_id_seq OWNED BY public.exercises.id;


--
-- Name: gym_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.gym_records (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    exercise_id integer NOT NULL,
    one_rm_kg numeric(6,2) NOT NULL,
    updated_at timestamp without time zone DEFAULT now(),
    recorded_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.gym_records OWNER TO postgres;

--
-- Name: gym_records_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.gym_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gym_records_id_seq OWNER TO postgres;

--
-- Name: gym_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.gym_records_id_seq OWNED BY public.gym_records.id;


--
-- Name: import_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.import_logs (
    id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    uploaded_by integer,
    type public.importtype NOT NULL,
    row_count integer,
    matched_count integer,
    unmatched_count integer,
    status public.importstatus,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.import_logs OWNER TO postgres;

--
-- Name: import_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.import_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.import_logs_id_seq OWNER TO postgres;

--
-- Name: import_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.import_logs_id_seq OWNED BY public.import_logs.id;


--
-- Name: import_mapping_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.import_mapping_configs (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    mapping json NOT NULL,
    updated_at timestamp without time zone DEFAULT now(),
    sample_file_name character varying(255),
    sample_file_path character varying(500)
);


ALTER TABLE public.import_mapping_configs OWNER TO postgres;

--
-- Name: import_mapping_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.import_mapping_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.import_mapping_configs_id_seq OWNER TO postgres;

--
-- Name: import_mapping_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.import_mapping_configs_id_seq OWNED BY public.import_mapping_configs.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    period character varying(20) NOT NULL,
    amount numeric(10,2) NOT NULL,
    paid boolean,
    paid_at timestamp without time zone
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: personal_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.personal_schedules (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    weekday integer NOT NULL,
    shift public.scheduleshift DEFAULT 'NONE'::public.scheduleshift NOT NULL
);


ALTER TABLE public.personal_schedules OWNER TO postgres;

--
-- Name: personal_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.personal_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.personal_schedules_id_seq OWNER TO postgres;

--
-- Name: personal_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.personal_schedules_id_seq OWNED BY public.personal_schedules.id;


--
-- Name: qualifying_times; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.qualifying_times (
    id integer NOT NULL,
    competition_id integer NOT NULL,
    event_type_id integer NOT NULL,
    category character varying(50),
    gender public.swimmergender,
    min_time_seconds numeric(10,2)
);


ALTER TABLE public.qualifying_times OWNER TO postgres;

--
-- Name: qualifying_times_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.qualifying_times_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.qualifying_times_id_seq OWNER TO postgres;

--
-- Name: qualifying_times_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.qualifying_times_id_seq OWNED BY public.qualifying_times.id;


--
-- Name: swimmer_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.swimmer_metrics (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    recorded_at date NOT NULL,
    weight_kg double precision,
    height_cm double precision,
    wingspan_cm double precision,
    notes text
);


ALTER TABLE public.swimmer_metrics OWNER TO postgres;

--
-- Name: swimmer_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.swimmer_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.swimmer_metrics_id_seq OWNER TO postgres;

--
-- Name: swimmer_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.swimmer_metrics_id_seq OWNED BY public.swimmer_metrics.id;


--
-- Name: swimmers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.swimmers (
    id integer NOT NULL,
    first_name_1 character varying(100) CONSTRAINT swimmers_first_name_not_null NOT NULL,
    last_name_1 character varying(100) CONSTRAINT swimmers_last_name_not_null NOT NULL,
    birth_date date,
    document_id character varying(50),
    gender public.swimmergender,
    category character varying(50),
    status public.swimmerstatus NOT NULL,
    status_reason character varying(255),
    status_updated_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    first_name_2 character varying(50),
    last_name_2 character varying(50),
    comuna character varying(100),
    institution character varying(150),
    phone character varying(30),
    email character varying(150),
    profile public.swimmerprofile,
    is_federated boolean DEFAULT false
);


ALTER TABLE public.swimmers OWNER TO postgres;

--
-- Name: swimmers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.swimmers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.swimmers_id_seq OWNER TO postgres;

--
-- Name: swimmers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.swimmers_id_seq OWNED BY public.swimmers.id;


--
-- Name: time_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.time_records (
    id integer NOT NULL,
    swimmer_id integer NOT NULL,
    event_type_id integer NOT NULL,
    time_seconds numeric(10,2) NOT NULL,
    recorded_date date NOT NULL,
    competition_id integer,
    source public.timesource NOT NULL,
    is_official boolean,
    location_note character varying(150)
);


ALTER TABLE public.time_records OWNER TO postgres;

--
-- Name: time_records_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.time_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.time_records_id_seq OWNER TO postgres;

--
-- Name: time_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.time_records_id_seq OWNED BY public.time_records.id;


--
-- Name: training_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.training_sessions (
    id integer NOT NULL,
    date date NOT NULL,
    category character varying(50),
    coach_id integer
);


ALTER TABLE public.training_sessions OWNER TO postgres;

--
-- Name: training_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.training_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.training_sessions_id_seq OWNER TO postgres;

--
-- Name: training_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.training_sessions_id_seq OWNED BY public.training_sessions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(150) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attendance_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs ALTER COLUMN id SET DEFAULT nextval('public.attendance_logs_id_seq'::regclass);


--
-- Name: attendances id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendances ALTER COLUMN id SET DEFAULT nextval('public.attendances_id_seq'::regclass);


--
-- Name: competitions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competitions ALTER COLUMN id SET DEFAULT nextval('public.competitions_id_seq'::regclass);


--
-- Name: convocatoria_entries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries ALTER COLUMN id SET DEFAULT nextval('public.convocatoria_entries_id_seq'::regclass);


--
-- Name: convocatorias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatorias ALTER COLUMN id SET DEFAULT nextval('public.convocatorias_id_seq'::regclass);


--
-- Name: event_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_types ALTER COLUMN id SET DEFAULT nextval('public.event_types_id_seq'::regclass);


--
-- Name: exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises ALTER COLUMN id SET DEFAULT nextval('public.exercises_id_seq'::regclass);


--
-- Name: gym_records id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gym_records ALTER COLUMN id SET DEFAULT nextval('public.gym_records_id_seq'::regclass);


--
-- Name: import_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs ALTER COLUMN id SET DEFAULT nextval('public.import_logs_id_seq'::regclass);


--
-- Name: import_mapping_configs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_mapping_configs ALTER COLUMN id SET DEFAULT nextval('public.import_mapping_configs_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: personal_schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personal_schedules ALTER COLUMN id SET DEFAULT nextval('public.personal_schedules_id_seq'::regclass);


--
-- Name: qualifying_times id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualifying_times ALTER COLUMN id SET DEFAULT nextval('public.qualifying_times_id_seq'::regclass);


--
-- Name: swimmer_metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.swimmer_metrics ALTER COLUMN id SET DEFAULT nextval('public.swimmer_metrics_id_seq'::regclass);


--
-- Name: swimmers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.swimmers ALTER COLUMN id SET DEFAULT nextval('public.swimmers_id_seq'::regclass);


--
-- Name: time_records id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.time_records ALTER COLUMN id SET DEFAULT nextval('public.time_records_id_seq'::regclass);


--
-- Name: training_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.training_sessions ALTER COLUMN id SET DEFAULT nextval('public.training_sessions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: attendance_logs attendance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_pkey PRIMARY KEY (id);


--
-- Name: attendances attendances_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_pkey PRIMARY KEY (id);


--
-- Name: competitions competitions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competitions
    ADD CONSTRAINT competitions_pkey PRIMARY KEY (id);


--
-- Name: convocatoria_entries convocatoria_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries
    ADD CONSTRAINT convocatoria_entries_pkey PRIMARY KEY (id);


--
-- Name: convocatorias convocatorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatorias
    ADD CONSTRAINT convocatorias_pkey PRIMARY KEY (id);


--
-- Name: event_types event_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_types
    ADD CONSTRAINT event_types_pkey PRIMARY KEY (id);


--
-- Name: exercises exercises_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_name_key UNIQUE (name);


--
-- Name: exercises exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_pkey PRIMARY KEY (id);


--
-- Name: gym_records gym_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gym_records
    ADD CONSTRAINT gym_records_pkey PRIMARY KEY (id);


--
-- Name: import_logs import_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs
    ADD CONSTRAINT import_logs_pkey PRIMARY KEY (id);


--
-- Name: import_mapping_configs import_mapping_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_mapping_configs
    ADD CONSTRAINT import_mapping_configs_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: personal_schedules personal_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personal_schedules
    ADD CONSTRAINT personal_schedules_pkey PRIMARY KEY (id);


--
-- Name: qualifying_times qualifying_times_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualifying_times
    ADD CONSTRAINT qualifying_times_pkey PRIMARY KEY (id);


--
-- Name: swimmer_metrics swimmer_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.swimmer_metrics
    ADD CONSTRAINT swimmer_metrics_pkey PRIMARY KEY (id);


--
-- Name: swimmers swimmers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.swimmers
    ADD CONSTRAINT swimmers_pkey PRIMARY KEY (id);


--
-- Name: time_records time_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.time_records
    ADD CONSTRAINT time_records_pkey PRIMARY KEY (id);


--
-- Name: training_sessions training_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.training_sessions
    ADD CONSTRAINT training_sessions_pkey PRIMARY KEY (id);


--
-- Name: attendance_logs uq_swimmer_date; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT uq_swimmer_date UNIQUE (swimmer_id, date);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_attendance_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_attendance_logs_id ON public.attendance_logs USING btree (id);


--
-- Name: ix_attendances_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_attendances_id ON public.attendances USING btree (id);


--
-- Name: ix_competitions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_competitions_id ON public.competitions USING btree (id);


--
-- Name: ix_convocatoria_entries_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_convocatoria_entries_id ON public.convocatoria_entries USING btree (id);


--
-- Name: ix_convocatorias_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_convocatorias_id ON public.convocatorias USING btree (id);


--
-- Name: ix_event_types_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_event_types_id ON public.event_types USING btree (id);


--
-- Name: ix_exercises_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_exercises_id ON public.exercises USING btree (id);


--
-- Name: ix_gym_records_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_gym_records_id ON public.gym_records USING btree (id);


--
-- Name: ix_import_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_import_logs_id ON public.import_logs USING btree (id);


--
-- Name: ix_import_mapping_configs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_import_mapping_configs_id ON public.import_mapping_configs USING btree (id);


--
-- Name: ix_payments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payments_id ON public.payments USING btree (id);


--
-- Name: ix_personal_schedules_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_personal_schedules_id ON public.personal_schedules USING btree (id);


--
-- Name: ix_qualifying_times_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_qualifying_times_id ON public.qualifying_times USING btree (id);


--
-- Name: ix_swimmer_metrics_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_swimmer_metrics_id ON public.swimmer_metrics USING btree (id);


--
-- Name: ix_swimmers_document_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_swimmers_document_id ON public.swimmers USING btree (document_id);


--
-- Name: ix_swimmers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_swimmers_id ON public.swimmers USING btree (id);


--
-- Name: ix_time_records_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_time_records_id ON public.time_records USING btree (id);


--
-- Name: ix_training_sessions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_training_sessions_id ON public.training_sessions USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: attendance_logs attendance_logs_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: attendances attendances_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.training_sessions(id);


--
-- Name: attendances attendances_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: convocatoria_entries convocatoria_entries_convocatoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries
    ADD CONSTRAINT convocatoria_entries_convocatoria_id_fkey FOREIGN KEY (convocatoria_id) REFERENCES public.convocatorias(id);


--
-- Name: convocatoria_entries convocatoria_entries_event_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries
    ADD CONSTRAINT convocatoria_entries_event_type_id_fkey FOREIGN KEY (event_type_id) REFERENCES public.event_types(id);


--
-- Name: convocatoria_entries convocatoria_entries_qualifying_time_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries
    ADD CONSTRAINT convocatoria_entries_qualifying_time_id_fkey FOREIGN KEY (qualifying_time_id) REFERENCES public.qualifying_times(id);


--
-- Name: convocatoria_entries convocatoria_entries_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatoria_entries
    ADD CONSTRAINT convocatoria_entries_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: convocatorias convocatorias_competition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatorias
    ADD CONSTRAINT convocatorias_competition_id_fkey FOREIGN KEY (competition_id) REFERENCES public.competitions(id);


--
-- Name: convocatorias convocatorias_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.convocatorias
    ADD CONSTRAINT convocatorias_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: gym_records gym_records_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gym_records
    ADD CONSTRAINT gym_records_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id);


--
-- Name: gym_records gym_records_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gym_records
    ADD CONSTRAINT gym_records_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: import_logs import_logs_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs
    ADD CONSTRAINT import_logs_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: payments payments_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: personal_schedules personal_schedules_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personal_schedules
    ADD CONSTRAINT personal_schedules_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: qualifying_times qualifying_times_competition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualifying_times
    ADD CONSTRAINT qualifying_times_competition_id_fkey FOREIGN KEY (competition_id) REFERENCES public.competitions(id);


--
-- Name: qualifying_times qualifying_times_event_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualifying_times
    ADD CONSTRAINT qualifying_times_event_type_id_fkey FOREIGN KEY (event_type_id) REFERENCES public.event_types(id);


--
-- Name: swimmer_metrics swimmer_metrics_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.swimmer_metrics
    ADD CONSTRAINT swimmer_metrics_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: time_records time_records_competition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.time_records
    ADD CONSTRAINT time_records_competition_id_fkey FOREIGN KEY (competition_id) REFERENCES public.competitions(id);


--
-- Name: time_records time_records_event_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.time_records
    ADD CONSTRAINT time_records_event_type_id_fkey FOREIGN KEY (event_type_id) REFERENCES public.event_types(id);


--
-- Name: time_records time_records_swimmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.time_records
    ADD CONSTRAINT time_records_swimmer_id_fkey FOREIGN KEY (swimmer_id) REFERENCES public.swimmers(id);


--
-- Name: training_sessions training_sessions_coach_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.training_sessions
    ADD CONSTRAINT training_sessions_coach_id_fkey FOREIGN KEY (coach_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict AHn5U41Qpg90Nuhfksa6kuGdQBzZOaGLoYb9Pfw7WYj0SFsd03Xi8hUbxcuopzf

