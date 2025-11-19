from openai import OpenAI
import base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

client = OpenAI(
    base_url='http://localhost:8025/v1/',

    # required but ignored
    api_key='ollama',
)

# response = client.chat.completions.create(
#     messages=[
#         {
#             'role': 'user',
#             'content': 'bạn tên gì',
#         }
#     ],
#     model='qwen3-vl:2b',
# )

# print(response.choices[0].message.content)

# path = "/home/tuanndq/test_chatbot/chatbot_tuan_v3/chatbot_base/bear.png"
# image_base64 = image_to_base64(path)
# messages = [
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "What is the capital of France?"}
# ]
# res1 = client.chat.completions.create(model='qwen3-vl:2b', messages=messages)

# messages += [res1.choices[0].message]
# messages += [{
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "What's in this image?"},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
#                     # "image_url": {"url": "/home/tuanndq/test_chatbot/chatbot_tuan_v3/chatbot_base/bear.png"}
#                 },
#             ],
#         }]

# res2 = client.chat.completions.create(model='qwen3-vl:2b', messages=messages)
# messages += [res2.choices[0].message]

# chat_completion_from_base64 = client.chat.completions.create(
#     messages=messages+[
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "What's in this image?"},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
#                     # "image_url": {"url": "/home/tuanndq/test_chatbot/chatbot_tuan_v3/chatbot_base/bear.png"}
#                 },
#             ],
#         },
#     ],
#     model="qwen3-vl:2b",
#     max_completion_tokens=500,
# )

# result = chat_completion_from_base64.choices[0].message.content
# print("Chat completion output from base64 encoded image:", result)
 



 # from openai import OpenAI
# client = OpenAI(
#     base_url='http://localhost:8025/v1/',
#     api_key='ollama',
# )

# response = client.responses.create(
#   model="qwen3:4b",
#   input="Write a one-sentence bedtime story about a unicorn."
# )

# print(response.output_text)

# chat_completion_from_base64 = client.chat.completions.create(
#     messages=[
#         {'role': 'user', 'content': [{'type': 'text', 'text': 'describe image'},
#                                     {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUTExIVFRUXGBUSFhUVFRUVFRUVFRUXFhUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OGxAQGi0dHx8tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tKy0tLS0tLS0tLS0rLS0tLS03K//AABEIAKMBNgMBIgACEQEDEQH/xAAcAAABBQEBAQAAAAAAAAAAAAAEAAIDBQYHAQj/xAA8EAABAwIEAwUGBAUDBQAAAAABAAIDBBEFEiExBkFREyJhcYEykaGxwfAHFNHhI0JSYvEzcoIVJJKiwv/EABkBAAMBAQEAAAAAAAAAAAAAAAECAwQABf/EACQRAAICAgICAgIDAAAAAAAAAAABAhEDIRIxBEEiMhNRQmFx/9oADAMBAAIRAxEAPwDllQwnVBORdTNbRBN1KZIRHrGXKNipinUcA3R7rAJJSColVILIZzlJM/VRWTR6FY4BIrzMvAUQHrSpmBRNCKhZdK2dRPAFFUy3PgFLKcoQbRc39w6pUysI0EQm5+9AiOfh0+pQ2bKLc+a9Emn3ouKILv1Nh05nzSfI0eSDFQBsMzlYYdgs852sPCwXdDd9AZqhyUgjzjbw219FvMM/DvS7yfJXMPA8TUHNHLE2cjqaAjUDkq57CDZdlq+Dmctd1i8e4Zc25A06oqSOljaMiJdLL1tQRz+f+EyohLTqowVREWzp/wCFPFfZTthe45HmwB2DjtZd5abhfIOHzmORj27tcD7ivq7hyq7amhlBvnY11/MJo6FeyxXieAlkRARlRkIjs07skbBQL2aXYors04NXcjuIH+XThAjA1ItQ5h4gvYJGBEry67kw0V01Mgp6Bp5K3kKCc+yZSYvFFPPhLbbLL47hgF1vy8ELN8QxgtJQlLWzkjCw4VcbJLTUcIsvVkWNF7OCS95yPpqTQKPDacudeytpo8oVmRA290kLyaS6jlfcqWGO5CWvYQZtNfko54bK8bFbkq7EhqgmwMq3MSDEXFHdE9gLJmwUVgRdK5ePp9U/LlF0shktkdU/M5Nc7KL89kwOP31UT3XKNFT0O/ylnJ02CYDmNgtVwrwu+d4Lh3VzaRyTk6QTwjw2ZCHWXV8KwdkQFhqnYNhDYWgNCt+zWdybZrjFRVEZcFC+RSTRoGVBMah0r1VYnStc03RMsiEqHkhGzqOYcW4YGXIGiyGi6VxbHeNxPQrmbFoxu0Y8ySkSsX05+FM2bDYAeQc30DtPhZfMbF9D/hBVXw9gvs94+VlRd0S9HQ7JwUbHJ6IB6V0y6V0KDY9eJt15ddR1j7pXTLpuZGgWSEphcoJZbICevy7rqOsPe7VCTNF0G7Ex1TJq8dUyBZ5NUhpsqrFJ8zSm4jLdwsowwluqWfQYlPFUluhSRNXTBJZ+LKWc3wrDdAmY0y2isYKnK0KlxecucrMkVcje8rWhptigYYzcFXtFslRx7PBYKhrIrrS1YJCqm05JQOAaal01UvZKw7HReuiQYSsfHzVZVTa+A28SjcUqgBlG6pZH3XRV7HSoe56ieP3TrqZkF9U/R22W/B2FdtKBbnqu34RhjYYwAFjPwnwyzHSEbuIHounvh7qy5JXJmzFDjFFNV18jNmNPqSqKq4zfGbPYLedk7iHHzT3H5eSR1rizTl9SAbLE1fHeZxZNSsbrlIuSRtvceIXQTfSGm4x7ZvqXi2J49oBGurmuGhXMoqWGTvw3b/b0PSy02Gwva3W6D0GOzQucCoZ2CyzOLYvIzRgVP/1msOuU2TRTYJSSCOOTlhcVzJi1vE2JvkhLXixBHrcrJNWjGqRjzSuRKxdu/BOrvC+In2XZgPQX+i4i1dG/CCtyVTRfQ3adepDdvMhM9NE1tM+gown2ULZdF72yYFk2VLKo2zJ4lQ2EdkSyJGRMdMEA0elqYUPJWDqhJcRb1C5TQGgqcqhxQ3BTqvFQAdVk8U4ktcWulyZoxW2Di2Orqot5oVuLKirsWL+SEjqyN1j/ACyb0VWNezcNqL2Kt4CC1YimxEELQYdX3C0wy2qYHCuiesXq8qj80k9gOPCocRYJgpzuooIzYK6w2m0udUWT9gTInW2REb7BXIGm3JZmsmIcbdUqGLpj9E2KwuVVRVZAXhqXFCwItih8RnsxMikcVFjFO7snO6C6Vv0MkZapmub9feoWdUwAkqQDTz+Sv0C7PYdx5rUYVQXyk8za1vHcFZeOBzy1jRdz3BrQNy5xs0e82XQ8Pp/y1R+Tms6eENMjgbtAzADKedszb+BvyKhmdI0+PTezoHCVL2UQb4uPvK1cMgsqamZYCyNY+yxKTuza4qqJcQgDmm651ivDTe17TsA5w2dfpsSDobLoLpbqPIDurJ+0Ta1T2YLh/hN/auec1nEOINjYi+1vT3LdVmGARbbKyo2gbBe4u+0ZT99iXWkcU4okmjd/Dic7ckgXyDrbmVSR1lWyJsrnXLnW7NzbHLyd4c9PJdXrKBsgvseoVecFbe7rHnsEVNJVQrxtu7OYcUvPZMLhYvN7eQJWajWu/EyQdrGwcg4+8gD5FZBq04/qZMv3JWrScF1GSqiI/rFreNgs21WOFS5JWO6EH3FFixPpo1iaasqvw6UuiY4ixLQSPMIkFatGW2Tfm3J7a5yHCS6kdbJZMVI5Ktq8aIXtUFR1xU8lJBUpDa3Gn8lWyV0h5qCrmCVB3ivNmk5F4t0R1VZJbcqonJO61NRQXCoK6HLuozhT2XgwRseiZlUrHaIWWVUhR2wiGQeStsKqyHWJ6LNRSWREdVYgot0FKzoz33ASQGGVGZgSWiLtWIzmFO02Ct6KqyDUKjjqLBP/ADiRvYlFxV4jcWGioJ37qOerUUJuqRToVsna5FUjeaiDFPESAkYUg6jsSjMbcBTuHUFAUQ1QGN1uYZR7IO3VApFFABYLxzdL+gRGQN7zjfoAmNaXuHv8gFazqPKSfs5on3tkex9wbEZXB1weS1OPU7o8RlklDv8ASzg6HvdkGC5O4uLm2tlj5iC7TbYImTEZnNEbpHOYLAAm+g2GbewsNLpJwctr/Bsc1Hs+kaIhzGuGxAPvF1M5UPA1bnpWNJ7zBkPkPZ+HyV/IFhqmejdoHdJZQSVa9mUcVNmKdAZqKRrQBYi/PVC4zYtOq59xBRz07+3jnksNCwucWkdLfXdDUeKVMrrC4B3Ltco+qeMv6JuCu7NJDLuDyUVbOACUObjc38VjOP8AHuzj7Jh77+n8rOZ8Og/ZFJydI5yUVZh+Jq7t6mR4N23yN8m6fO59VWvGyUTLoh8WwWxKlR5zbk7IYnLXcE8OvqHiUtJiYbuFvaA3AWSjZZy+jOCqeNtJETlazICToM19SiuwPSLukogGgN9m2nkpvyaY3H6fOIxmJJDQQNLn1VyLKvJk+KKk0iglisrx4CrK2wXcznAo6ySyz9dOrHF6iyyNbWHqsHk+Q0+KHx4r2RVk1ynYZVZSq50lynRuWNN9l+KNxBMHBU2PRjVBU2IFotdeVNZmuqp2gVRRSykKIm6dWusVFG/ZBRoawkxpkjLIkjRQSbjzRkUiazAJe4vE7CoCG3HNJaMd8SUuzlcj1FmXsqizKlEWeP3R9CFXOOqsqAap0tCeyxLFI1ilDFKGKNFUgac5WE8zoqWrqG8hc8v1VnjU2gFlQ5STsmivbH6VHjWk6lPmflbpufkpMlhd233og5HXNymWwPSGx2HmvYhme0dSF45h32CtMDoSXBxCMnSBGLbo6lwhIYw0jbYjqFtu1uFieH290LSRzZfJYZ9npQ6HVV+Sz1S6ujc5zZY8h9kEEEdQXWPyWqY0OFwhsTw9z2ENNvH9kuykWk7aswVbjlc099jnDwLZGE+X7KTBeJHlxbLG+52dkI15302Tp8AqQ72gR98kRIWUsZdK4X3JPyCeNj5p42tBGOYuyGIyONgNupPIALkFfWvnkc9w1cfEkDk3wARfEGNPqpNyI2+y3/6Pih4mZR4/d1rxw4qzycuTk6XRJRwga9N/ElSBl3H72UjG2aP/ACPny+ibCPr8U5Mjq4LEHkfmuq8IuLqVlySBpvsucSAFvXYELonBTbQlvQ/4XJ/JBa+LNbw5SAzgn+W59VoaqqMZ7x31QfD0OWMyW1cbDyCpuN6xzWscOpCpN0rImgGJgjdU+MYrYaFYWPHnA7lMrcTLhuVjyeUktDxg2PxHFC7S6rS0lR7lWkbBZZEnLbNKXFUVLo7J4R9TFoqrtLaLqphHSy2QzqtMnlQWfVVSJ+x87rryCXUJPQ4f3guOZeh9wmBuo80ynfoioG3cPNBlI9GywgdxJT4bH3AvFrgtEX2cYlj0Q3ZlWjok/DcJlneI4mOe88gNh1J2A8Susmylc03VxgtJJI60cb3noxrnW87DRdNwD8MoIwHVZM0mh7Nji2JvgSNX/ALe0UAiaGRMZEwbNY0NHwVorWxa2cog4QrnDSlf65W/MpVPDFZGC59O8AdLO+DSV1uWqy+08n1VbPicr9ImZvkg4IdSo4RUdmSczu9qNb3HhbkoJTG0d3vHoBb3krffijgZEEdSYwybPkdYDvtI0uOZHVYSnw6V4vkOuwDT6lT412U5X0VM8hJu70aNglBATrb9FtsA4IkqZG9ozs4xa42Luvqp+KuHW01SYmizcoc3y2+i5ukGMbZkYKAuIJ1Wjw+jtyU1JRq0gplnlKzTGFFvgA5K6k2VVhMVijsTmyhTsskV78WdC7q3p+indxXGR7VvA6LP1sucqnqwAuSC3RfYrxfHG0kuv4DUrmOO41LVPzPNmg91nIeJ6lLFZ87srdhug5W8ui14oJdmDNkctLo9omXd5a+4XR8Mdy0dQD7z+yHwxvecP7Sj6YfxWD+1v10VGyUUPqI9T6Ae+/0Q40A93rqrKoZof9wPw1/VBSMuCPHT4oIZodT6hw+910Tgokh48Gnz2WBoIyTbnt53IXSOEGBsrnHYFgIHoSilbOeonTaRmSJjTyAWe47pmvpHu5t7w9Fpp6ckZgbi11nOJ2E00zf7CqtJpoizjgOqKCKpcMLtbFWEeGW5FYH40pFI5FEpgrCmnFkWaLwThQi2yrHw5pDfnTAKmoFt1UOcratowqWbQqM8bi9lIyTIpkA82JRcj1XznVGMQMnz3UT263ShKKMdwhVMDVodSTKygqNQqaMEIht10l7Gg9HQcMxHu7pLF02IObokqKaJvsHwLDJKqZsMQuTqXfysbzc49Pmuz4BgkVJH2UO51fIfae76DoEJwrgDaGARgh0rrGaTq7+kf2jYK+hatMIcdkbsexoChqZbbboghTYbS3Oc+n6ohAaTB3P1kuByb+qvKWiawWaLBFxhSEJbGSK6voo5LB7Q7QjUXtdAUnD0EZu1gCuKkaJBCjrA3UDRsAFi/wAQsLz9jKBqM0Z+Y+RW+kcqbGYO0hcOhDx6HX4EoTVxY8HUkc4pMJPRXFNhXgr+koxZGNpgFiaN1lDHRW5IHH6c9ndaw04KGr6AOaQlaGUkc1jpnO2BVDxLTvjA5F2g+pXYMPwpjRsuZ/iLJmqsg2aAB5ndUitiTejEQwBocfTzKBexW9YywAH2VXTtWlMySRDTS5HB33bmj5XZXtcNRsPQ3HzVVLvboFY0R7RmX+Zuo8bbfouYI/ou5tW3HOzv2+aEyXA8CiMJfnY5h5beR+oKY+O3v/z8vigmPJew/h+EOlaT1zHwAv8Aottw9Ysc7Ulz3HQchYBZbBYv4b37X023vyC6NglD2UDGga2ufM6lVh2SmtGy4cqe0haDo5uhHlsosfoQ6N9v6XfJUlBM+J+YHzHVX7a1kzS0mxII8r+Cbpk/RhcOogBsj30jeiMqcLkjHs5h1bqPXp6qpq8RtorwolLQ91O3wSFO0jkqn/qYPNIYgOq0JaI3skxGkbbZYbGILOJC0+IV3isrilRfmsXlJcTVidFY9qgfCpmvTXuXlc2aRkbEWCLIUPXrpl1thTpD3OU0J0VZLMnw1dlSadCxlssrJIUVK8We5DaO/RjXVFsCihaiWNXssyodl0VlTDugeCCaEewJWMiTZSNcmNN15ayUIp23CTdgUsyUB0+C44bK1BFljrsdD5FWAHJQTMXHGeByOLehI/RTiZNxaKzw7+oWPmP2shg5YpqnRvh8kmGGVMDrocKRiSx6JSbBcl4zi/7t58LrqFZLZpPQErmHE0lm3PtOJKaL+QHH42ZOYXd6E/fwVZM3U+CtHDQ+Nh6DUqvk9r1WkyyK5rdfNSU7iyRp8R7joQvWjvBSzssfiiLRe0hyS35OFz9+qOq6cf8AF2v7eBVc09xrugI95uB7x8VeYeM+Vp19kjz139ynZZdF7wnhDpZGDdjP4jr6Au/launNo2211VfwvRBkTRz3J81oREtMVSMs3bK007RyCgks0g2Vq+FAVlMTawJ1GwRYofESNQVkvxFw5phbM0ZX5shtoHggm5HUEb+K1BqWxsGbVw/lB+ZWcxmV0zSXdRYcgNdkYrdiujmDIXdSvJIXdStoMLCa/CwqKbR3BM53NFJf2ioW0bua6BLg4Q7sISSjyO6MX+RKHkpHLbS4ag5MPWaXjfodTMc6AqF8RWukw9BzYcoPHJD2mZR8RUfZkLRSYch30PgmcgKJTZivUfJSL1JaDR9GsisiI2r2MKVrV6LInlkZEh8qmalYSay8Lk0PXpShPCUyB+pCRCjvqicGO6pj06M3Ca48kAldiUV4z4d4em/wuqZgWleFQTR5XFvTby5KGaPs04JehoCcF61qa9Zno1ICxU9w+Nh8VyrjF95Q0fyj47n5rqeIvs2/K64/jBLqp9+R+pujh3KzszqFFfUnKLdBb9fkq5+gv4/ojKw3dYfd0HV9By+ytRjZC6OxPqfv0U8wvl9P3TqhuoHUW99l6/TKuOJ/aGUf1NA9Ln6LccJ0RfJG4DS1h/x0+ixFCy/nr8efusF0rgqmL4mi1gL+d7H/AB6IL7DP62dCwlhZYW7pvY+Otx8PmrwgAXuqowNEWYaG2Ya6jne6AkxB7xrvbVaKsytltVV7W7alVFRiDjzKEkJUWZOkI2Pc66U5sAvGhQYtLbKPNMuxRrnhNMgQJnTHTJnA5TLDMEx1lX/mF6KldwDzsmlYg5Ywp+3UT3JkhGwKSFCSwqwkQz0rghlNldJEh3wqxeFC4KUsKKLIVslLdeKwLUlP8A3M7MxEMXqSoxEOUjUkkrGPSE0r1JAJ4SoZkklyASMO6c/l5JJIHCVTiY7zfEfVJJJk+hbD9iFqilSSWGZtgVeK/wCm5cgqT/GlPNeJJ8Hs7P6Ah/qO++QVa/2h5JJLSZGFvHeb98yo38vI/JJJccHYS27z5fVdQ4TNiANs+3m0X+S9SS/yKP6G2abxtHp/7FDFouV6ktaMUiCcINySSZCEkarsfPeb/tSSTR7AyrukUklUQjcowUklwB117dJJcE8KieF6kuZwO8KFwXiSVhInBJJJA4//2Q=='}}]}
#         , {'role': 'assistant', 'content': 
#            [{'type': 'text', 'text': '\n\nHình ảnh cho thấy một người phụ nữ với mái tóc dài, uốn lượn, màu nâu sẫm. Cô mặc một chiếc váy trắng có cổ chữ V sâu và phần cánh tay rộng, tạo dáng vẻ thanh lịch. Nền ảnh là cảnh ngoài trời, với cây xanh mờ và đường nhựa, gợi cảm giác thư giãn, tự nhiên. Ánh sáng dịu nhẹ làm nổi bật vẻ đẹp của người mẫu, cùng với đôi khuyên tai vàng nhỏ, tăng thêm nét sang trọng.'}]}, 
#         {'role': 'user', 'content': [{'type': 'text', 'text': 'bạn biết người phụ nữ trên là ai không'}]}]
# ,
#     model="qwen3-vl:2b",
#     max_completion_tokens=500,
# )

# result = chat_completion_from_base64.choices[0].message.content
# print("Chat completion output from base64 encoded image:", result)


chat_completion_from_base64 = client.chat.completions.create(
    messages=[
        {'role': 'system', 'content': 'You are a helpful AI assistant. Based on the conversation between User and assistant.\nJust answer the last question of User and do nothing else. Always respond in Vietnamese language only.'},
        {'role': 'user', 'content': [{'type': 'text', 'text': 'tell me a joke'}]}
    ]
,
    model="qwen3-vl:2b",
    max_completion_tokens=500,
)

result = chat_completion_from_base64.choices[0].message.content
print("Chat completion output from base64 encoded image:", result)