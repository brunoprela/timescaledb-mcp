#!/usr/bin/env python3
"""Test database connection from host."""
import asyncio
import asyncpg

async def main():
    try:
        # Try without password (trust auth should work)
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            database='postgres',
            password=None  # Explicitly set to None
        )
        await conn.close()
        print("✅ Host connection works!")
        return 0
    except TypeError:
        # If password=None doesn't work, try without the parameter
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='postgres',
                database='postgres'
            )
            await conn.close()
            print("✅ Host connection works!")
            return 0
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return 1
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(asyncio.run(main()))

