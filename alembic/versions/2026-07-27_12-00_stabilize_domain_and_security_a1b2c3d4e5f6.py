"""stabilize domain and security

Revision ID: a1b2c3d4e5f6
Revises: 48e8ddc168b3
Create Date: 2026-07-27 12:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "48e8ddc168b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "patronymic_name",
        existing_type=sa.String(length=100),
        nullable=True,
    )
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
        existing_comment="пароль пользователя",
        comment="хеш пароля пользователя",
    )
    op.alter_column(
        "users",
        "is_deleted",
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_comment="флаг удаленности пользователя",
        comment="флаг удаления пользователя",
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT lower(email)
                FROM users
                GROUP BY lower(email)
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Duplicate user emails differing only by case must be resolved';
            END IF;
        END
        $$;
        """
    )
    op.execute("UPDATE users SET email = lower(email)")
    op.create_index(
        "uix_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )
    op.alter_column(
        "users_to_rooms",
        "is_chief",
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_comment="является ли лидером команды",
        comment="является ли руководителем комнаты",
    )
    op.alter_column(
        "teams",
        "is_chief",
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_comment="является ли лидером команды",
        comment="является ли руководителем команды",
    )
    op.alter_column(
        "teams",
        "role",
        server_default="неопределена",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "teams",
        "tag",
        server_default="неопределена",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )

    op.add_column(
        "teams_to_rooms",
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=True,
            comment="название команды",
        ),
    )
    op.execute(
        """
        UPDATE teams_to_rooms AS team_entity
        SET name = COALESCE(
            (
                SELECT MIN(team_member.name)
                FROM teams AS team_member
                WHERE team_member.team_id = team_entity.team_id
            ),
            'Команда-' || LEFT(team_entity.team_id::text, 8)
        )
        """
    )
    op.alter_column("teams_to_rooms", "name", nullable=False)

    op.execute(
        """
        DELETE FROM teams AS team_member
        USING teams_to_rooms AS team_entity
        WHERE team_member.team_id = team_entity.team_id
          AND team_member.room_id <> team_entity.room_id
        """
    )
    op.execute(
        """
        DELETE FROM teams AS duplicate
        USING teams AS original
        WHERE duplicate.team_id = original.team_id
          AND duplicate.user_id = original.user_id
          AND duplicate.id > original.id
        """
    )
    op.drop_constraint("uix_team_user_room", "teams", type_="unique")
    op.drop_column("teams", "name")
    op.drop_column("teams", "room_id")
    op.create_unique_constraint(
        "uix_team_user",
        "teams",
        ["team_id", "user_id"],
    )

    op.execute("ALTER TYPE status RENAME VALUE 'is_executor' TO 'assigned'")
    op.execute("ALTER TYPE status RENAME VALUE 'is_not_executor' TO 'unassigned'")
    op.execute("ALTER TYPE difficulty RENAME VALUE 'unknowed' TO 'unknown'")
    op.execute(
        """
        UPDATE tasks
        SET status = CASE
            WHEN executor IS NULL THEN 'unassigned'::status
            ELSE 'assigned'::status
        END
        WHERE status IN ('assigned'::status, 'unassigned'::status)
        """
    )
    op.execute(
        """
        UPDATE tasks
        SET status = 'completed'::status
        WHERE is_completed = true
        """
    )
    op.execute(
        """
        UPDATE tasks
        SET task_finish_date = COALESCE(
            task_finish_date,
            task_update_date,
            task_create_date
        )
        WHERE status = 'completed'::status
        """
    )
    op.drop_column("tasks", "is_completed")
    op.add_column(
        "tasks",
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="дата мягкого удаления",
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "deleted_by",
            sa.Uuid(),
            nullable=True,
            comment="пользователь, удаливший задачу",
        ),
    )
    op.create_foreign_key(
        "fk_tasks_deleted_by_users",
        "tasks",
        "users",
        ["deleted_by"],
        ["user_id"],
    )
    op.create_check_constraint(
        "ck_tasks_status_executor",
        "tasks",
        "(status NOT IN ('assigned', 'in_progress') OR executor IS NOT NULL) "
        "AND (status <> 'unassigned' OR executor IS NULL)",
    )
    op.create_check_constraint(
        "ck_tasks_completed_finish",
        "tasks",
        "status <> 'completed' OR task_finish_date IS NOT NULL",
    )

    op.create_index(
        "ix_users_to_rooms_room_id",
        "users_to_rooms",
        ["room_id"],
    )
    op.create_index(
        "ix_tasks_team_status",
        "tasks",
        ["team_id", "status"],
    )
    op.create_index(
        "ix_tasks_executor_status",
        "tasks",
        ["executor", "status"],
    )
    op.create_index(
        "ix_tasks_team_finish_date",
        "tasks",
        ["team_id", "task_finish_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_team_finish_date", table_name="tasks")
    op.drop_index("ix_tasks_executor_status", table_name="tasks")
    op.drop_index("ix_tasks_team_status", table_name="tasks")
    op.drop_index("ix_users_to_rooms_room_id", table_name="users_to_rooms")

    op.drop_constraint("ck_tasks_completed_finish", "tasks", type_="check")
    op.drop_constraint("ck_tasks_status_executor", "tasks", type_="check")
    op.drop_constraint("fk_tasks_deleted_by_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "deleted_by")
    op.drop_column("tasks", "deleted_at")
    op.add_column(
        "tasks",
        sa.Column(
            "is_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.execute("UPDATE tasks SET is_completed = (status = 'completed'::status)")
    op.execute("ALTER TYPE difficulty RENAME VALUE 'unknown' TO 'unknowed'")
    op.execute("ALTER TYPE status RENAME VALUE 'unassigned' TO 'is_not_executor'")
    op.execute("ALTER TYPE status RENAME VALUE 'assigned' TO 'is_executor'")

    op.drop_constraint("uix_team_user", "teams", type_="unique")
    op.add_column(
        "teams",
        sa.Column("room_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "teams",
        sa.Column("name", sa.String(length=50), nullable=True),
    )
    op.execute(
        """
        UPDATE teams AS team_member
        SET room_id = team_entity.room_id,
            name = team_entity.name
        FROM teams_to_rooms AS team_entity
        WHERE team_member.team_id = team_entity.team_id
        """
    )
    op.alter_column("teams", "room_id", nullable=False)
    op.alter_column("teams", "name", nullable=False)
    op.create_foreign_key(
        "fk_teams_room_id_rooms",
        "teams",
        "rooms",
        ["room_id"],
        ["room_id"],
    )
    op.create_unique_constraint(
        "uix_team_user_room",
        "teams",
        ["team_id", "user_id", "room_id"],
    )
    op.drop_column("teams_to_rooms", "name")

    op.alter_column(
        "teams",
        "tag",
        server_default=None,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "teams",
        "role",
        server_default=None,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "teams",
        "is_chief",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "users_to_rooms",
        "is_chief",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "is_deleted",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.execute("UPDATE users SET patronymic_name = '' WHERE patronymic_name IS NULL")
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "patronymic_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.drop_index("uix_users_email_lower", table_name="users")
