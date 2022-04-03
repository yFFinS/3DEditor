#version 330

layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec4 aColor;

out vec4 oColor;

struct InstanceProps
{
    mat4 Model;
    mat4 MVP;
};

uniform InstanceProps Instance;

void main()
{
    gl_Position = Instance.MVP * vec4(aPosition, 1.0f);
    oColor = aColor;
}