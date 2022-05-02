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
vec3 SELECTED_COLOR = vec3(0.7, 0.7, 1);

void main()
{
    gl_Position = Instance.MVP * vec4(aPosition, 1.0f);
    if (Instance.Selected < 0)
        oColor = aColor;
    else
        oColor = vec4(SELECTED_COLOR, aColor.w);
}