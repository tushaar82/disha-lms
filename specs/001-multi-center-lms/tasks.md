# Tasks: Multi-Center Student Learning & Satisfaction Management System

**Input**: Design documents from `/specs/001-multi-center-lms/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks grouped by user story (P1-P5) for independent implementation

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story (US1-US5)

---

## Phase 1: Setup (16 tasks)

- [x] T001 Create Django project: `django-admin startproject config .`
- [x] T002 Create requirements.txt (Django 5.0+, DRF, pytest, psycopg2, redis, celery)
- [x] T003 Create requirements-dev.txt (black, flake8, mypy, bandit, django-debug-toolbar)
- [x] T004 [P] Create .env.example
- [x] T005 [P] Create package.json (Tailwind 3.4+, DaisyUI 4.0+)
- [x] T006 [P] Create tailwind.config.js
- [x] T007 [P] Create pytest.ini
- [x] T008 Setup config/settings/ (base.py, development.py, production.py)
- [x] T009 Configure base.py (INSTALLED_APPS, MIDDLEWARE, TEMPLATES, DATABASES)
- [x] T010 Configure development.py (DEBUG=True, SQLite, Debug Toolbar)
- [x] T011 Configure production.py (PostgreSQL, security, Redis)
- [x] T012 Create config/urls.py
- [x] T013 [P] Create templates/base.html (Tailwind, DaisyUI, Google Charts)
- [x] T014 [P] Create templates/components/
- [x] T015 [P] Create static/css/ and static/js/
- [x] T016 [P] Create .gitignore

---

## Phase 2: Foundational (29 tasks) ⚠️ CRITICAL

### Core App (8 tasks)
- [x] T017 Create apps/core/ app
- [x] T018 Create TimeStampedModel in apps/core/models.py
- [x] T019 Create SoftDeleteModel in apps/core/models.py
- [x] T020 Create AuditLog model in apps/core/models.py
- [x] T021 [P] Create apps/core/mixins.py
- [x] T022 [P] Create apps/core/utils.py
- [x] T023 [P] Create apps/core/middleware.py
- [x] T024 [P] Create apps/core/templatetags/

### Authentication (11 tasks)
- [x] T025 Create apps/accounts/ app
- [x] T026 Create custom User model in apps/accounts/models.py
- [x] T027 Create UserManager in apps/accounts/models.py
- [x] T028 Configure AUTH_USER_MODEL in settings
- [x] T029 Create apps/accounts/permissions.py (IsMasterAccount, IsCenterHead, IsFaculty)
- [x] T030 Create apps/accounts/forms.py
- [x] T031 Create apps/accounts/views.py (Login, Logout, Profile)
- [x] T032 Create apps/accounts/urls.py
- [x] T033 Create apps/accounts/templates/accounts/login.html
- [x] T034 Create apps/accounts/templates/accounts/profile.html
- [x] T035 Run makemigrations and migrate

### API Setup (10 tasks)
- [x] T036 Create apps/api/ app
- [x] T037 Create apps/api/v1/ directory
- [x] T038 Create apps/api/v1/serializers.py (UserSerializer)
- [x] T039 Create apps/api/v1/views.py (LoginAPIView, LogoutAPIView, MeAPIView)
- [x] T040 Create apps/api/v1/permissions.py
- [x] T041 Create apps/api/v1/urls.py
- [x] T042 Configure DRF settings
- [x] T043 Install drf-spectacular
- [x] T044 Create API docs URLs

**Checkpoint**: Foundation ready

---

## Phase 3: US1 - Faculty Attendance (Priority: P1) 🎯 MVP (29 tasks)

### Models (8 tasks)
- [x] T045 [P] [US1] Create apps/centers/ and Center model
- [x] T046 [P] [US1] Create apps/students/ and Student model
- [x] T047 [P] [US1] Create apps/faculty/ and Faculty model
- [x] T048 [P] [US1] Create apps/subjects/ and Subject model
- [x] T049 [P] [US1] Create Topic model
- [x] T050 [P] [US1] Create Assignment model
- [x] T051 [US1] Create apps/attendance/ and AttendanceRecord model
- [x] T052 [US1] Run migrations

### Views & Templates (10 tasks)
- [x] T053 [US1] Create TodayAttendanceView in apps/attendance/views.py
- [x] T054 [US1] Create MarkAttendanceView
- [x] T055 [US1] Create AttendanceForm in apps/attendance/forms.py
- [x] T056 [US1] Create attendance services (calculate_session_duration, check_if_backdated)
- [x] T057 [US1] Create apps/attendance/urls.py
- [x] T058 [US1] Create templates/attendance/today.html
- [x] T059 [US1] Create templates/attendance/mark_form.html
- [x] T060 [US1] Create AddTopicView in apps/subjects/views.py
- [x] T061 [US1] Create TopicForm
- [x] T062 [US1] Create templates/subjects/add_topic.html

### API (6 tasks)
- [x] T063 [P] [US1] Create AttendanceRecordSerializer
- [x] T064 [P] [US1] Create TopicSerializer
- [x] T065 [US1] Create AttendanceViewSet
- [x] T066 [US1] Create TodayAttendanceAPIView
- [x] T067 [US1] Create BulkAttendanceAPIView
- [x] T068 [US1] Add attendance endpoints to API URLs

### UI Polish (5 tasks)
- [x] T069 [US1] Add time picker JavaScript
- [x] T070 [US1] Add multi-select for topics
- [x] T071 [US1] Add "Completed" status confirmation modal
- [x] T072 [US1] Add toast notifications
- [x] T073 [US1] Add loading states

**Checkpoint**: Faculty can mark attendance - MVP functional!

---

## Phase 4: US2 - Admin Center Management (Priority: P2) (34 tasks)

### Student Management (13 tasks)
- [x] T074 [US2] Create StudentListView, StudentCreateView, StudentDetailView, StudentUpdateView, StudentDeleteView
- [x] T075 [US2] Create StudentForm, AssignmentForm
- [x] T076 [US2] Create apps/students/urls.py
- [x] T077 [US2] Create templates/students/student_list.html
- [x] T078 [US2] Create templates/students/student_form.html
- [x] T079 [US2] Create templates/students/student_detail.html
- [x] T080 [US2] Create AssignSubjectView
- [x] T081 [US2] Create AssignFacultyView
- [x] T082 [US2] Create templates/students/assign_subject.html
- [x] T083 [US2] Create templates/students/assign_faculty.html
- [x] T084 [US2] Create ReadyForTransferView
- [x] T085 [US2] Create templates/students/ready_for_transfer.html
- [ ] T086 [US2] Create BackdatedAttendanceView
- [ ] T087 [US2] Create templates/attendance/backdated_form.html

### Faculty Management (6 tasks)
- [x] T088 [P] [US2] Create FacultyListView, FacultyCreateView, FacultyDetailView, FacultyUpdateView
- [x] T089 [P] [US2] Create FacultyForm
- [x] T090 [P] [US2] Create apps/faculty/urls.py
- [x] T091 [US2] Create templates/faculty/faculty_list.html
- [x] T092 [US2] Create templates/faculty/faculty_form.html
- [x] T093 [US2] Create templates/faculty/faculty_detail.html

### Subject Management (6 tasks)
- [x] T094 [P] [US2] Create SubjectListView, SubjectCreateView, SubjectDetailView, SubjectUpdateView
- [x] T095 [P] [US2] Create SubjectForm
- [x] T096 [P] [US2] Create apps/subjects/urls.py
- [x] T097 [US2] Create templates/subjects/subject_list.html
- [x] T098 [US2] Create templates/subjects/subject_form.html
- [x] T099 [US2] Create templates/subjects/subject_detail.html

### API (7 tasks)
- [x] T100 [P] [US2] Create StudentSerializer, AssignmentSerializer
- [x] T101 [P] [US2] Create FacultySerializer, SubjectSerializer
- [x] T102 [US2] Create StudentViewSet
- [x] T103 [US2] Create FacultyViewSet
- [x] T104 [US2] Create SubjectViewSet
- [x] T105 [US2] Create AssignmentViewSet
- [x] T106 [US2] Add US2 endpoints to API URLs

### Dashboard (3 tasks)
- [x] T107 [US2] Create CenterDashboardView
- [x] T108 [US2] Create templates/centers/dashboard.html
- [x] T109 [US2] Create templates/components/sidebar.html

**Checkpoint**: Admin can manage center operations

---

## Phase 5: US3 - Master Account Multi-Center (Priority: P3) (22 tasks)

### Center Management (6 tasks)
- [x] T110 [US3] Create CenterListView, CenterCreateView, CenterDetailView, CenterUpdateView, CenterDeleteView
- [x] T111 [US3] Create CenterForm
- [x] T112 [US3] Create apps/centers/urls.py
- [x] T113 [US3] Create templates/centers/center_list.html
- [x] T114 [US3] Create templates/centers/center_form.html
- [x] T115 [US3] Create templates/centers/center_detail.html

### Context Switching (6 tasks)
- [x] T116 [US3] Create AccessCenterDashboardView
- [x] T117 [US3] Implement session-based center context
- [x] T118 [US3] Create center context middleware
- [x] T119 [US3] Update CenterDashboardView for Master Account
- [x] T120 [US3] Add "Switch Center" button in navbar
- [x] T121 [US3] Create audit log for center access

### Cross-Center Reporting (5 tasks)
- [x] T122 [US3] Create apps/reports/ app
- [x] T123 [US3] Create AllCentersReportView
- [x] T124 [US3] Create calculate_center_metrics() service
- [x] T125 [US3] Create templates/reports/all_centers.html
- [x] T126 [US3] Add Google Charts for center comparison

### API (5 tasks)
- [x] T127 [P] [US3] Create CenterSerializer
- [x] T128 [US3] Create CenterViewSet
- [x] T129 [US3] Create CenterHeadSerializer
- [x] T130 [US3] Create CenterHeadViewSet
- [x] T131 [US3] Add US3 endpoints to API URLs

**Checkpoint**: Master Account can manage multiple centers

---

## Phase 6: US4 - Reporting & Analytics (Priority: P4) (26 tasks)

### Report Services (7 tasks)
- [x] T132 [US4] Create CenterReportView
- [x] T133 [US4] Create StudentReportView
- [x] T134 [US4] Create FacultyReportView
- [x] T135 [US4] Create InsightsView
- [x] T136 [US4] Create attendance/learning velocity services
- [x] T137 [US4] Create insights services (at-risk, extended, nearing completion)
- [x] T138 [US4] Create chart data preparation services

### Report Templates (8 tasks)
- [x] T139 [US4] Create templates/reports/center_report.html
- [x] T140 [US4] Create templates/reports/student_report.html with Gantt chart
- [x] T141 [US4] Add timeline visualization
- [x] T142 [US4] Create templates/reports/faculty_report.html
- [x] T143 [US4] Create templates/reports/insights.html
- [x] T144 [US4] Add column chart for subject completion
- [x] T145 [US4] Add pie chart for attendance distribution
- [ ] T146 [US4] Add date range filters

### Export (3 tasks)
- [x] T147 [P] [US4] Create ExportReportPDFView
- [x] T148 [P] [US4] Create ExportReportCSVView
- [x] T149 [US4] Add export buttons

### API (5 tasks)
- [x] T150 [P] [US4] Create CenterReportAPIView
- [x] T151 [P] [US4] Create StudentReportAPIView
- [x] T152 [P] [US4] Create FacultyReportAPIView
- [x] T153 [US4] Create InsightsAPIView
- [x] T154 [US4] Add US4 endpoints to API URLs

### Caching (3 tasks)
- [ ] T155 [US4] Install and configure Redis
- [ ] T156 [US4] Add cache decorators
- [ ] T157 [US4] Implement cache invalidation

**Checkpoint**: Comprehensive reporting functional

---

## Phase 7: US5 - Feedback & Satisfaction (Priority: P5) (32 tasks)

### Models (4 tasks)
- [x] T158 [P] [US5] Create apps/feedback/ app
- [x] T159 [US5] Create FeedbackSurvey model
- [x] T160 [US5] Create FeedbackResponse model
- [x] T161 [US5] Run migrations

### Survey Management (6 tasks)
- [x] T162 [US5] Create SurveyListView, SurveyCreateView, SurveyDetailView, SurveyUpdateView
- [x] T163 [US5] Create SurveyForm
- [x] T164 [US5] Create apps/feedback/urls.py
- [x] T165 [US5] Create templates/feedback/survey_list.html
- [x] T166 [US5] Create templates/feedback/survey_form.html
- [x] T167 [US5] Create templates/feedback/survey_detail.html

### Email Sending (6 tasks)
- [ ] T168 [US5] Configure email backend
- [ ] T169 [US5] Create send_survey_email() Celery task
- [ ] T170 [US5] Create SendSurveyView
- [ ] T171 [US5] Create email template
- [ ] T172 [US5] Generate unique survey links
- [ ] T173 [US5] Install and configure Celery

### Survey Response (5 tasks)
- [ ] T174 [US5] Create SubmitSurveyView (public)
- [ ] T175 [US5] Create templates/feedback/survey_public.html
- [ ] T176 [US5] Add validation (expiry, token)
- [ ] T177 [US5] Save responses
- [ ] T178 [US5] Update student satisfaction_score

### Satisfaction Reporting (5 tasks)
- [ ] T179 [US5] Create SurveyResponsesView
- [ ] T180 [US5] Create templates/feedback/responses.html
- [ ] T181 [US5] Add rating distribution chart
- [ ] T182 [US5] Add faculty-wise breakdown
- [ ] T183 [US5] Create satisfaction trends service

### API (6 tasks)
- [ ] T184 [P] [US5] Create SurveySerializer, ResponseSerializer
- [ ] T185 [US5] Create SurveyViewSet
- [ ] T186 [US5] Create SendSurveyAPIView
- [ ] T187 [US5] Create SubmitSurveyAPIView (public)
- [ ] T188 [US5] Create SurveyResponsesAPIView
- [ ] T189 [US5] Add US5 endpoints to API URLs

**Checkpoint**: Feedback system functional

---

## Phase 8: Polish & Production (35 tasks)

### Offline Support (6 tasks)
- [ ] T190 [P] Create service-worker.js
- [ ] T191 [P] Create manifest.json
- [ ] T192 Create offline-attendance.js (IndexedDB)
- [ ] T193 Implement Background Sync API
- [ ] T194 Add offline indicator
- [ ] T195 Add sync status indicator

### Security (7 tasks)
- [ ] T196 [P] Run check --deploy
- [ ] T197 [P] Configure HTTPS redirect
- [ ] T198 [P] Set secure cookie flags
- [ ] T199 [P] Configure CSP headers
- [ ] T200 [P] Add rate limiting
- [ ] T201 [P] Run Bandit scan
- [ ] T202 [P] Run Safety check

### Performance (6 tasks)
- [ ] T203 [P] Add database indexes
- [ ] T204 [P] Optimize queries
- [ ] T205 [P] Configure Redis caching
- [ ] T206 [P] Add pagination
- [ ] T207 [P] Compress static assets
- [ ] T208 [P] Configure CDN

### Accessibility (6 tasks)
- [ ] T209 [P] Run axe-core audit
- [ ] T210 [P] Add ARIA labels
- [ ] T211 [P] Test keyboard navigation
- [ ] T212 [P] Test screen reader
- [ ] T213 [P] Check color contrast
- [ ] T214 [P] Add skip links

### Documentation (5 tasks)
- [ ] T215 [P] Create docs/architecture.md
- [ ] T216 [P] Create docs/deployment.md
- [ ] T217 [P] Create docs/api.md
- [ ] T218 [P] Update README.md
- [ ] T219 [P] Create CONTRIBUTING.md

### Deployment (5 tasks)
- [ ] T220 [P] Create Dockerfile
- [ ] T221 [P] Create docker-compose.yml
- [ ] T222 [P] Create deployment scripts
- [ ] T223 [P] Configure CI/CD pipeline
- [ ] T224 [P] Setup monitoring

---

## Summary

**Total Tasks**: 223
- Phase 1 (Setup): 16 tasks
- Phase 2 (Foundational): 29 tasks ⚠️ CRITICAL
- Phase 3 (US1 - MVP): 29 tasks 🎯
- Phase 4 (US2): 34 tasks
- Phase 5 (US3): 22 tasks
- Phase 6 (US4): 26 tasks
- Phase 7 (US5): 32 tasks
- Phase 8 (Polish): 35 tasks

**Parallel Opportunities**: 89 tasks marked [P]

**MVP Path**: Complete Phase 1 → Phase 2 → Phase 3 (US1) = 74 tasks

**Incremental Delivery**: After MVP, add US2 → US3 → US4 → US5 independently
