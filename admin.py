# 管理员命令脚本
from flask import Flask
from models import db, User
from config import Config
import click
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin(username, email, password):
    """创建管理员用户
    
    参数:
        username: 管理员用户名
        email: 管理员邮箱
        password: 管理员密码
    """
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f'用户 {username} 已存在!')
            return
        
        # 创建新管理员用户
        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'管理员用户 {username} 创建成功!')

@app.cli.command('list-users')
def list_users():
    """列出所有用户"""
    with app.app_context():
        users = User.query.all()
        if not users:
            click.echo('没有找到任何用户')
            return
        
        click.echo('用户列表:')
        for user in users:
            click.echo(f'ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 管理员: {"是" if user.is_admin else "否"}')

@app.cli.command('reset-password')
@click.argument('username')
@click.argument('new_password')
def reset_password(username, new_password):
    """重置用户密码
    
    参数:
        username: 用户名
        new_password: 新密码
    """
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo(f'用户 {username} 不存在!')
            return
        
        user.set_password(new_password)
        db.session.commit()
        click.echo(f'用户 {username} 的密码已重置!')

if __name__ == '__main__':
    app.run(debug=True)