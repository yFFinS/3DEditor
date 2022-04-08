#version 330

layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec4 aColor;

out vec4 oColor;

struct InstanceProps
{
    mat4 MVP;
    float Selected;
};

uniform InstanceProps Instance;

void main()
{
    gl_Position = Instance.MVP * vec4(aPosition, 1.0f);
    if (Instance.Selected < 0)
        oColor = aColor;
    else
        oColor = vec4(54 / 256f, 225 / 256f, 247 / 256f, aColor.w);
}