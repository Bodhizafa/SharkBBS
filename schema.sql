DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id TINYTEXT PRIMARY KEY,
    nick TINYTEXT,
    avatar TINYTEXT,
    signature TEXT,
    password_sha256 SMALLBLOB,
);

DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
    users_id TINYTEXT,
    role TINYTEXT,
    FOREIGN KEY(users_id) REFERENCES users(id)
)

DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
    id INTEGER PRIMARY KEY ASC,
    users_id TINYTEXT,
    thread_id INTEGER,
    content TEXT,
    FOREIGN KEY(users_id) REFERENCES users(id),
    FOREIGN KEY(thread_id) REFERENCES posts(id)
);

INSERT INTO passwords (id, hash) VALUES
    (0, NULL),
    (1, 'b60efdd7fb69c8ef063935f4d7eddad40eb82ee4'); -- "beans"

INSERT INTO users VALUES
    ("root", "DJ Testio", "/prophat.jpg", "When one has a great deal to put into it, a day has a hundred pockets.\n\t- Nietzsche", 1);

INSERT INTO roles VALUES
    ('root', 'admin')
    ('root', 'moderator')
    ('root', 'poster')
    ('root', 'reader')

INSERT INTO posts VALUES
    (0, "root", 0, "ROOT POST TEST");
