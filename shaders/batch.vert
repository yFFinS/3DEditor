#version 330

layout (location = 0) in vec3 aPosition;
layout (location = 1) in vec4 aColor;

out vec4 oColor;

struct BatchProps
{
    mat4 Mat_PV;
};

uniform BatchProps Batch;

void main()
{
    gl_Position = Batch.Mat_PV * vec4(aPosition, 1.0f);
    oColor = aColor;
}