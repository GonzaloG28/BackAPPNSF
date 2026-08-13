--
-- PostgreSQL database dump
--

\restrict AHpP7jpvOhmsdAqHg3ZwC6ed3hzK1R2cdWiIGePpeQ0Y63ajRAZQHDzisuV0f6K

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
-- Data for Name: attendance_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attendance_logs (id, swimmer_id, date, complied) FROM stdin;
10	1	2026-08-11	t
11	3	2026-08-11	t
12	5	2026-08-11	t
\.


--
-- Data for Name: attendances; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attendances (id, swimmer_id, date, session_id, shift) FROM stdin;
5	1	2026-08-01	\N	ABSENT
6	2	2026-08-01	\N	ABSENT
7	1	2026-08-04	\N	ABSENT
9	3	2026-08-04	\N	ABSENT
8	2	2026-08-04	\N	ABSENT
10	1	2026-08-05	\N	ABSENT
11	2	2026-08-05	\N	ABSENT
12	3	2026-08-05	\N	ABSENT
14	1	2026-08-07	\N	AM_PM
15	2	2026-08-07	\N	AM_PM
16	3	2026-08-07	\N	AM_PM
17	1	2026-08-08	\N	AM_PM
18	2	2026-08-08	\N	AM_PM
19	3	2026-08-08	\N	AM_PM
\.


--
-- Data for Name: competitions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.competitions (id, name, organizer, date, location, max_events_per_swimmer) FROM stdin;
5	Prueba	\N	2000-04-10	Prueba	3
6	Pueba	\N	2000-10-03	Prueba	3
\.


--
-- Data for Name: convocatoria_entries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.convocatoria_entries (id, convocatoria_id, swimmer_id, event_type_id, qualifying_time_id, best_time_seconds, selected, time_record_date) FROM stdin;
6	5	5	1	\N	\N	t	\N
\.


--
-- Data for Name: convocatorias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.convocatorias (id, competition_id, created_by, status, created_at) FROM stdin;
6	6	\N	DRAFT	2026-08-10 22:36:27.778068
5	5	\N	EXPORTED	2026-08-09 22:51:35.30522
\.


--
-- Data for Name: event_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.event_types (id, name, distance_m, stroke) FROM stdin;
1	50m Libre	50	FREE
2	100m Libre	100	FREE
3	100m Pecho	100	BREAST
4	200m Libre	200	FREE
5	50m Espalda	50	BACK
6	100m Mariposa	100	FLY
\.


--
-- Data for Name: exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.exercises (id, name) FROM stdin;
1	Sentadilla
2	Press banca
3	Peso muerto
4	Dominadas
5	Press militar
\.


--
-- Data for Name: gym_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.gym_records (id, swimmer_id, exercise_id, one_rm_kg, updated_at, recorded_at) FROM stdin;
2	2	2	150.00	2026-08-08 13:05:18.340241	2026-08-11 21:36:10.427682
3	2	1	120.00	2026-08-08 13:05:28.895585	2026-08-11 21:36:10.427682
1	3	1	160.00	2026-08-08 20:04:23.482619	2026-08-11 21:36:10.427682
4	5	1	154.30	2026-08-09 17:00:47.013219	2026-08-11 21:36:10.427682
5	5	2	87.30	2026-08-10 21:20:31.130442	2026-08-11 21:36:10.427682
\.


--
-- Data for Name: import_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.import_logs (id, file_name, uploaded_by, type, row_count, matched_count, unmatched_count, status, created_at) FROM stdin;
1	excel_prueba_roster.xlsx	\N	ROSTER	3	3	0	SUCCESS	2026-07-31 21:34:58.031256
\.


--
-- Data for Name: import_mapping_configs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.import_mapping_configs (id, name, mapping, updated_at, sample_file_name, sample_file_path) FROM stdin;
1	Plantilla principal	{}	2026-08-10 23:31:26.158159	\N	\N
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, swimmer_id, period, amount, paid, paid_at) FROM stdin;
\.


--
-- Data for Name: personal_schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.personal_schedules (id, swimmer_id, weekday, shift) FROM stdin;
7	3	6	NONE
1	3	0	AM_PM
2	3	1	AM_PM
3	3	2	AM_PM
4	3	3	AM_PM
5	3	4	AM_PM
6	3	5	AM_PM
8	1	0	AM_PM
9	1	1	AM_PM
10	1	2	AM_PM
11	1	3	AM_PM
12	1	4	AM_PM
13	1	5	AM_PM
14	5	0	AM_PM
15	5	1	AM_PM
16	5	2	AM_PM
17	5	3	AM_PM
18	5	4	AM_PM
19	5	5	AM
\.


--
-- Data for Name: qualifying_times; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.qualifying_times (id, competition_id, event_type_id, category, gender, min_time_seconds) FROM stdin;
8	5	1	OPEN	MALE	30.00
\.


--
-- Data for Name: swimmer_metrics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.swimmer_metrics (id, swimmer_id, recorded_at, weight_kg, height_cm, wingspan_cm, notes) FROM stdin;
1	3	2026-08-05	50	175	\N	\N
2	5	2026-08-09	80	1.86	\N	\N
\.


--
-- Data for Name: swimmers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.swimmers (id, first_name_1, last_name_1, birth_date, document_id, gender, category, status, status_reason, status_updated_at, created_at, first_name_2, last_name_2, comuna, institution, phone, email, profile, is_federated) FROM stdin;
1	Juan	Pérez	2010-05-14	12345678-9	\N	\N	ACTIVE	\N	\N	2026-07-31 21:34:58.037193	\N	\N	\N	\N	\N	\N	\N	f
2	María	Soto	2011-08-20	98765432-1	\N	\N	ACTIVE	\N	2026-08-03 21:01:38.121551	2026-07-31 21:34:58.046176	\N	\N	\N	\N	\N	\N	\N	f
3	Diego	Muñoz	2009-03-02	\N	\N	\N	ACTIVE	\N	2026-08-04 23:22:24.68208	2026-07-31 21:34:58.0492	\N	\N	\N	\N	\N	\N	\N	f
5	Gonzalo	Gimenez	2007-03-28	22362329-8	MALE	Todo Competidor	ACTIVE	\N	2026-08-10 23:25:32.337115	2026-08-09 16:52:49.787758	Lionel	Briones	Temuco	VIU	974036405	gonzalogimenez280@gmail.com	\N	f
\.


--
-- Data for Name: time_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.time_records (id, swimmer_id, event_type_id, time_seconds, recorded_date, competition_id, source, is_official, location_note) FROM stdin;
1	1	1	28.45	2026-07-31	\N	IMPORT	f	\N
2	1	2	62.10	2026-07-31	\N	IMPORT	f	\N
3	2	3	75.30	2026-07-31	\N	IMPORT	f	\N
5	3	5	35.20	2026-07-31	\N	IMPORT	f	\N
6	3	6	72.50	2026-07-31	\N	IMPORT	f	\N
4	3	4	135.00	2026-07-31	\N	IMPORT	f	Nacional
7	1	2	102.11	2010-03-10	\N	TRAINING	f	Nacional
8	5	1	28.00	2000-03-10	\N	TRAINING	f	Prueba
9	5	3	NaN	2026-06-18	\N	TRAINING	f	\N
10	5	3	NaN	2026-06-18	\N	TRAINING	f	\N
11	5	3	NaN	2026-06-18	\N	TRAINING	f	\N
12	5	3	NaN	2026-06-18	\N	TRAINING	f	Nacional
13	5	3	60.10	2026-06-18	\N	TRAINING	f	Nacional
\.


--
-- Data for Name: training_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.training_sessions (id, date, category, coach_id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, full_name, email, hashed_password, is_active, created_at) FROM stdin;
1	Gonzalo Profesor	gonzalo@test.cl	$2b$12$GXQJxHJljJ6X8ZxFI0L9SuOB2O0LzXBkkOYdjwugQKgexMQOBQFnK	t	2026-08-02 19:40:29.579544
2	Admin	admin@test.cl	$2b$12$AygpXmp2KTWfHHnAXe4vOurGtAhIauzh0MFSacUV2uBNFlmJ/GYy6	t	2026-08-09 20:16:43.280121
\.


--
-- Name: attendance_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendance_logs_id_seq', 12, true);


--
-- Name: attendances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendances_id_seq', 19, true);


--
-- Name: competitions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.competitions_id_seq', 6, true);


--
-- Name: convocatoria_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.convocatoria_entries_id_seq', 6, true);


--
-- Name: convocatorias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.convocatorias_id_seq', 6, true);


--
-- Name: event_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.event_types_id_seq', 6, true);


--
-- Name: exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.exercises_id_seq', 5, true);


--
-- Name: gym_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.gym_records_id_seq', 5, true);


--
-- Name: import_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.import_logs_id_seq', 1, true);


--
-- Name: import_mapping_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.import_mapping_configs_id_seq', 1, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 1, false);


--
-- Name: personal_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.personal_schedules_id_seq', 19, true);


--
-- Name: qualifying_times_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.qualifying_times_id_seq', 8, true);


--
-- Name: swimmer_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.swimmer_metrics_id_seq', 2, true);


--
-- Name: swimmers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.swimmers_id_seq', 14, true);


--
-- Name: time_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.time_records_id_seq', 13, true);


--
-- Name: training_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.training_sessions_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


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

\unrestrict AHpP7jpvOhmsdAqHg3ZwC6ed3hzK1R2cdWiIGePpeQ0Y63ajRAZQHDzisuV0f6K

