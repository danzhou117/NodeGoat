# Shared black-box pytest suite

This suite verifies the NodeGoat contract over HTTP with `httpx` and directly
against MongoDB with `pymongo`; it does not import application code. It runs
unchanged against the Node app today and the FastAPI port later. It pins
current behavior, including vulnerabilities and quirks. A failure against the
FastAPI port means that port differs from NodeGoat: change the port, not this
test suite.

## Requirements

Python 3.11 or newer, MongoDB 4.4, and Node are required. The `mongodb@2.x`
Node driver used by the app cannot connect to MongoDB 6 or newer. Node is
needed for the default database reseed command.

The pinned dependencies are `pytest==9.2.0` (uploaded 2026-10-27),
`httpx==0.28.1` (uploaded 2024-12-06), and `pymongo==4.20.0` (uploaded
2026-11-12). PyMongo 4.20.0 connects to MongoDB 4.4.30.

```sh
python3 -m venv tests_shared/.venv
tests_shared/.venv/bin/pip install -r tests_shared/requirements.txt
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `BASE_URL` | `http://localhost:4000` | HTTP base URL for NodeGoat or the FastAPI port |
| `MONGODB_URI` | `mongodb://localhost:27017/nodegoat` | MongoDB database inspected by the suite |
| `DB_RESET_CMD` | `node artifacts/db-reset.js` | Reseed command run from the repository root |

Every test first runs `DB_RESET_CMD` from the repository root with
`MONGODB_URI` exported, then checks that reseeding produced three users, three
allocations, and a `counters.userId` sequence of 3. The suite wipes that
database; never point it at data you care about.

## Run against the Node app now

### Option A: local app and MongoDB

1. Start MongoDB 4.4 on `localhost:27017` (or use another local MongoDB 4.4):

   ```sh
   docker run -d --name nodegoat-mongo -p 27017:27017 mongo:4.4
   ```

2. Install the app dependencies and start the app in a separate terminal:

   ```sh
   npm ci --omit=dev
   npm start
   ```

3. Install the test dependencies and run from the repository root:

   ```sh
   python3 -m venv tests_shared/.venv
   tests_shared/.venv/bin/pip install -r tests_shared/requirements.txt
   tests_shared/.venv/bin/pytest tests_shared
   ```

This path was verified on the host's Node v26.12. The repository CI
configuration uses Node 10, 12, and 14.

### Option B: Docker Compose

```sh
docker compose -f docker-compose.yml -f tests_shared/docker-compose.shared-tests.yml up -d --build
DB_RESET_CMD="docker compose exec -T web node artifacts/db-reset.js" \
  tests_shared/.venv/bin/pytest tests_shared
```

The override publishes only the MongoDB service on host port 27017 so the
Python driver can inspect it. The container Node version verified for this
path is v12.22.12.

Each verified option collected 52 tests with no failures, skips, or xfails.
Option A took approximately 7.5 seconds per run; Option B took approximately
10.6 seconds per run.

## Run against the FastAPI port later

1. Keep MongoDB and the seed data contract in place, and start the FastAPI
   port against the same `MONGODB_URI`.
2. Stop the Node app first, or use a different HTTP port so the two apps are
   not confused.
3. Set the FastAPI address and run the unchanged suite:

   ```sh
   BASE_URL=http://localhost:<port> tests_shared/.venv/bin/pytest tests_shared
   ```

4. Reseeding can use the host Node runtime with `npm ci --omit=dev` and the
   repository's `artifacts/db-reset.js`, the Compose `web` container with
   `DB_RESET_CMD="docker compose exec -T web node artifacts/db-reset.js"`, or
   a replacement `DB_RESET_CMD` that produces identical documents.

## Parity checklist for the port

- Protected and successful redirects are HTTP 302 with relative `Location` values: `/dashboard`, `/benefits`, `/login`, and `/`. FastAPI's default redirect is 307, so set the status explicitly.
- POSTs to `/signup`, `/contributions`, `/profile`, `/memos`, and `/benefits` render their page directly with HTTP 200 instead of redirecting.
- A session survives across requests through a cookie; the cookie name is not part of the contract.
- The collections are `users`, `allocations`, `contributions`, `memos`, and `counters`, with the exact field sets asserted by the tests.
- User `_id`, allocation and contribution `userId`, counter `seq`, and contribution percentages are integers, not doubles or strings; allocation and memo `_id` values are BSON `ObjectId` values.
- Profile values written by the update flow are strings, and memo `timestamp` is a BSON date.
- Signup takes the next `counters.userId` value and writes a matching allocation. Node writes the allocation asynchronously, so the suite polls for it for up to five seconds.
- Random allocation values satisfy `stocks` 1-40, `funds` 1-40, and `bonds = 100 - stocks - funds`.
- Random signup benefit dates use `YYYY-MM-DD`, with month `00`-`11`, day `00`-`28`, and year 1-30 years ahead.
- The exact success strings are `"Contributions updated successfully."`, `"Profile updated successfully."`, and `"Benefits updated successfully."`.
- The exact login strings are `"Invalid username"` and `"Invalid password"`.
- The exact signup validation strings are `"User name already in use. Please choose another"`, `"Password must match"`, `"Invalid email address"`, and `"Password must be 8 to 18 characters including numbers, lowercase and uppercase letters."`.
- The exact contribution validation strings are `"Invalid contribution percentages"` and `"Contribution percentages cannot exceed 30 %"`.
- The exact profile validation string is `"Bank Routing number does not comply with requirements for format specified"`.
- The error page contains `"Oops.."`; missing allocations also contain `"ERROR: No allocations found for the user"`.

## Pinned insecure and quirky behavior

- `test_bad_username_is_echoed_and_distinguished` and `test_bad_password_is_distinguished`: invalid usernames and passwords receive distinct messages, and an invalid username is echoed.
- `test_signup_empty_email_accepts_weak_password`: empty email is omitted and weak plaintext passwords are accepted.
- `test_contribution_eval_is_pinned` and `test_non_numeric_contribution_is_server_error`: contribution inputs are evaluated as expressions (`2+3` stores integer 5), while non-numeric input produces a 500 error page.
- `test_other_users_allocations_are_visible`: any logged-in user can view any `/allocations/<id>`.
- `test_non_admin_can_update_benefits`: non-admin users can read and update `/benefits`.
- `test_unanchored_routing_regex_is_pinned`: `abc123#xyz` passes the routing-number check and is stored verbatim.
- `test_valid_profile_update`: the `website` profile field is silently dropped.
- `test_blank_profile_names_are_not_overwritten`: blank profile fields do not overwrite existing values.
- `test_memos_are_global`: memos are visible to all users.
- `test_missing_allocations_is_server_error`: `/allocations/<unknown>` returns HTTP 500 with `"ERROR: No allocations found for the user"`.

## Coverage and exclusions

- `test_seed.py`: seeded users, counters, allocations, and empty write collections.
- `test_auth.py`: login, logout, session guards, and anonymous write protection.
- `test_signup.py`: signup rendering, persistence, allocation creation, IDs, and validation.
- `test_contributions.py`: defaults, valid and invalid updates, replacement, and expression evaluation.
- `test_allocations.py`: own, cross-user, and missing allocation responses.
- `test_profile.py`: profile rendering, updates, blank fields, and routing validation.
- `test_memos.py`: rendering, Markdown storage, ordering, timestamps, and global visibility.
- `test_benefits.py`: admin listing and updates plus missing non-admin authorization.

Not covered: the allocations `threshold` filter, `/research`, `/learn`,
`/tutorial`, CSRF, and security headers.
