from openai import OpenAI

client = OpenAI(api_key="dummy", base_url="http://gx10:8000/v1")

# response = client.chat.completions.create(
#     model="motif/motif-3",
#     messages=[{"role": "user", "content": "Hello!"}]
# )

# print(response.choices[0].message.content)


response = client.responses.create(
    model="gpt-oss-120b",
    input="What is 123 * 456?"
)

print(response.output_text)