"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2025-06-13 04:51:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firstname', sa.String(), nullable=True),
        sa.Column('lastname', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('user_image', sa.String(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("gender IN ('male', 'female', 'other')", name='gender_types')
    )

    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_name', sa.String(), nullable=True),
        sa.Column('property_type', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('property_image', sa.String(), nullable=True),
        sa.Column('property_model', sa.String(), nullable=True),
        sa.Column('total_earnings', sa.Float(), nullable=True),
        sa.Column('total_generation', sa.Float(), nullable=True),
        sa.Column('total_used', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("property_type IN ('residential', 'commercial', 'industrial', 'agricultural')", name='property_types')
    )

    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('device_type', sa.String(), nullable=True),
        sa.Column('device_status', sa.String(), nullable=True),
        sa.Column('device_address', sa.String(), nullable=True),
        sa.Column('power_produced', sa.Float(), nullable=True),
        sa.Column('device_latitude', sa.Float(), nullable=True),
        sa.Column('device_longitude', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('config', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id'),
        sa.CheckConstraint("device_type IN ('inverter', 'battery', 'meter', 'sensor')", name='device_types'),
        sa.CheckConstraint("device_status IN ('active', 'inactive', 'maintenance', 'error')", name='device_status_types')
    )

    # Create power_generations table
    op.create_table(
        'power_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('today_power_generation', sa.Float(), nullable=True),
        sa.Column('today_date', sa.DateTime(), nullable=True),
        sa.Column('today_earning', sa.Float(), nullable=True),
        sa.Column('today_used', sa.Float(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create my_homes table
    op.create_table(
        'my_homes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('producing', sa.Float(), nullable=True),
        sa.Column('consuming', sa.Float(), nullable=True),
        sa.Column('charging', sa.Float(), nullable=True),
        sa.Column('exporting', sa.Float(), nullable=True),
        sa.Column('climate', sa.String(), nullable=True),
        sa.Column('rain_percentage', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    # Drop tables
    op.drop_table('my_homes')
    op.drop_table('power_generations')
    op.drop_table('devices')
    op.drop_table('properties')
    op.drop_table('users') 