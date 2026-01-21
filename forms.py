# 表单定义
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import User

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=20, message='用户名长度必须在3-20个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, message='密码长度不能少于6个字符')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')
    
    def validate_username(self, field):
        """验证用户名是否已存在"""
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('该用户名已被使用')
    
    def validate_email(self, field):
        """验证邮箱是否已存在"""
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')