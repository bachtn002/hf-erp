#API BASE


1. [Vietnamese](#vietnamese)
2. [English](#english)

## <a name="#vietnamese"></a>Mô tả

Mục địch module API BASE được xây dựng nhằm giúp cải thiện quá trình viết API trong Odoo. Tăng tốc sử lý vấn đề, 
bỏ qua các yêu cầu đặc thì của việc viết API như Authenticate, Authorization, Verify data, ...

Module này được thiết để theo hướng RestAPI, vậy lên vui nếu bạn chưa có nhiều kinh nghiệm khi làm việc với RestAPI 
vui lòng cập nhật tại [Restfulapi](https://restfulapi.net) hoặc tại 
[RESTful API là gì? Cách thiết kế RESTful API](https://topdev.vn/blog/restful-api-la-gi/)

##### Các thư viện cần cài khi sử dụng module

```pip install pyjwt```

##### Một vài lưu ý khi sử dụng module

<b>Request Header</b>

* Context-Type: application/json
* Access-Token: {access_token} ```Trong trường hợp người dùng đăng nhập```

<b>Request Body</b>

* Server sẽ chỉ nhận dữu liệu trong jsonrequest

## Các thành phần

### Bộ thư viện tiện ích

Chứ toàn bộ những gì có thể giúp bạn tăng tốc độ việc API. Các sử dụng đơn giản như sau.

> from {odoo_addons}.ev_api_base.controllers.helper import Route, {...}

####Các thành phần có trong helpers
  
  1. [ApiException](#api_exception)
  
  2. [Authentication](#authentication)

  3. [Dispatch](#dispatch)

  4. [Email](#email)

  5. [Filter](#filter)

  6. [Html](#html)

  7. [Logger](#logger)

  8. [Middleware](#middleware)

  9. [Pager](#pager)

  10. [Params](#params)

  11. [PhoneNumber](#phone_number)

  12. [Query](#query)

  13. [Response](#response)

  14. [Route](#route)

### Các controller cơ bản 

  1. [filters](#filters)
  2. [sign_in](#sign_in)
  3. [sign_up](#sign_up)
  4. [logout](#logout)
  5. [forgot_password](#forgot_password)

### Các model chức năng

  1. [Thiết bị đăng nhập](#user_device)
  2. [Logger api](#logger_api)


## Cách viết một API áp dụng module API BASE
  ```
  from odoo.http import Controller, route
  from addons_custom.ev_api_base.controllers.helpers import Route, Reponse, middleware


  class ResPartnerController(Controller):

      @route(route=Route('res_partners'), methods=['GET'], type='json', auth='none')
      @middleware(auth='user')
      def get_res_partners(self):
          `Lấy dữ liệu res partner tại đây`

          return Response.success(message=message, data=data}).to_json()

      @route(route=Route('res_partner'), method=['POST'], type='json', auth='none')
      @middleware(auth='user')
      def create_partner(self):
          `Thêm mới res partner tại đây`

          return Response.success(message, partner_id).to_json()

      .......
  ```

  hoặc bạn cũng có thể sử dụng cách sau(được sử dụng ở version trước 1.0.0).

  ```
  from odoo.http import Controller, route
  from addons_custom.ev_api_base.controllers.helpers import Route, Reponse, Dispatch


  class ResPartnerController(Controller):

      @route(route=Route('res_partners'), methods=['GET'], type='json', auth='none')
      def get_res_partners(self):
          try:
              data = Dispatch.dispatch(self, '_get_res_partners', verify=verify)
              return Response.success(message=message, data=data}).to_json()
          except ApiException as e:
              return e.to_json()

      def _get_res_partners(self):
          data = self.env['res.partner'].search([])
          return data

      .......
  ```

---


# Chi tiết thành phần

<a name="#api_exception"></a>
### ApiException

Quản lý toàn bộ exception được trả về cho client. 
    
1. Danh sách mã lỗi mặc định trả về

| Code                      | Mã                             |
| ------------------------  | ------------------------------ |
| ERROR                     | 400                            |
| AUTHORIZED                | 401                            |
| FORBIDDEN                 | 403                            |
| NOT_FOUND                 | 404                            |
| PARAM_NOT_PROVIDE         | 406                            |
| INVALID_ACCESS_TOKEN      | 407                            |
| INVALID_DATA_TYPE         | 408                            |
| INVALID_DATA_FORMAT       | 409                            |
| VALUE_NOT_NULL            | 410                            |
| UNKNOWN_ERROR             | 411                            |
| METHOD_NOT_FOUND          | 412                            |
| ACCESS_DENIED             | 413                            |

Có thể cập nhật thêm hoặc thay đổi mã code cũng như code sao cho phù hợp với dự án.

2. Định dạng dữ liệu trả về
```
{ 
  code: Mã lỗi,
  message: str,
  data: dict|list|...
}
```

3. Phương thức

```to_json()```

4. Cách sử dụng

```raise ApiException(message, code)```

``` return ApiException(message, code).to_json() ```


<a name="#authentication"></a>
### Authentication

Chứa các phương thức xác thực người dùng, generate access_token hay kiểm tra quyền người dùng đang đăng nhập.

<b>Lưu ý: Bạn sẽ phải cấu hình lại __KEY khi thay đổi môi trường deploy để đảm bảo tính an toàn cho API của mình. 
Đây là 1 chuỗi 16 ký tự bất kỳ phần biệt hoa thường.</b>

<a name="#dispatch"></a>
### Dispatch

Đảm kiểm việc điều hướng, verify dữ liệu, authentication khi người dùng sử dụng API

1. dispatch

```dispatch(ins, action: str, verify: list = [], auth: str = 'user', additional_params: dict = {})```

Trong đó:

| Tham số           | Kiểu dữ liệu  | Mô tả                                                                  |
|-------------------|---------------|------------------------------------------------------------------------|
| ins               | Controller    | Đối tượng Controller mà bạn đang sử dụng để gọi dispatch               |
| action            | string        | Tên hàm mà bạn muốn gọi tới                                            |
| verify            | list          | Danh sách các rule để kiểm soát dữ liệu gửi lên                        |
| auth              | string        | Xác thực api có cần người dùng đăng nhập hay không(user,none,both)     |
| additional_params | dict          | Danh sách tham số + dữ liệu mà bạn muốn gửi kèm                        |

Cách sử dụng:

```
class ResPartner(Controller):

    def get_partners(self, **kw):

        res = Dispatch.dispatch(self, '_get_partner')
    
    def _get_partners(self):

        return []

    def create_partner(self, **kw):

        res = Dispatch.dispatch(ResPartnerRepository(), 'create')


class ResPartnerRepository(Controller):

    def create(self):

        print(self._cr)
        print(self.env)
        print(self.params)
        print(self.context)

        return partner_id 
  ```

Sau khi function được gọi thông qua hàm dispatch thì <b>self</b> của hàm đó sẽ được thay đổi lại như sau: 

self._cr: request.cr
self.env: request.env(user=```user_id của người dùng đăng nhập hoặc 1```)
self.params: Tham số được gửi lên
self.context: Mặc định ```lang=vi_VN```



<a name="#email"></a>
### Email

Đơn giản hoá việc kiểm tra định dạng email

1. Phương thức

```validate(email, error_message='')```

Trong đó:

| Tham số           | Kiểu dữ liệu  | Mô tả                                    |
|-------------------|---------------|------------------------------------------|
| email             | string        | Email muốn kiểm tra                      |
| error_message     | string        | Thông điệp thông báo khi có lỗi          |

<a name="#filter"></a>
### Filter

Quản lý khi bạn muốn làm việc với 1 vài loại dữ liệu tĩnh cần cấu hình cho client từ server.
<b>Lưu ý: Vì dữ liệu là đã phần là tĩnh nên sẽ được lưu trên RAM để đơn giản công việc. Vì vậy khi khai báo nên
khai báo ngay tại hảm __init__ của Controller cho đơn giản
</b>

1. Phương thức

```push(filter: dict, override=False)```

Trong đó:

| Tham số           | Kiểu dữ liệu  | Mô tả                                    |
|-------------------|---------------|------------------------------------------|
| filter            | dict          | Dữ liệu filter                           |
| override          | boolean       | Ghi đề dữ liệu đã tồn tại                |

<b>Lưu ý: filter có thể chứa hàm callback để lấy dữu liệu từ database</b>


<a name="#html"></a>
### Html

Giúp sử lý các vấn đề khi làm việc với dữ liệu định dạng Html như xoá html tag, gắn thêm domain của hosting hiện tại 
vào đường dẫn ảnh tương đối.

1. Tham số

``` URL_ROOT : Trả về domain ```

Các sử dụng

```
  Html().URL_ROOT
  ```

2. Phương thức

```clear_html_tag(text: str = '')```

Trong đó:

| Tham số           | Kiểu dữ liệu  | Mô tả                                    |
|-------------------|---------------|------------------------------------------|
| str               | string        | Dữ liệu có chứa html tag                 |

Cách sử dụng

```
print( Html.clear_html_tag('<h1>HelloWorld</h1>') )

$ HelloWorld
  ```
3. Phương thức

```remake_image_src(html_str: str = '')```

Trong đó:

| Tham số           | Kiểu dữ liệu  | Mô tả                                    |
|-------------------|---------------|------------------------------------------|
| html_str          | string        | Dữ liệu có chứa html                     |

Cách sử dụng

```
print( Html().remake_image_src('<img src='/web/image/blog.post/1/image_1920/hello_world.png'/>
<img src='https://helloworld.vn/hello_world.png'/>') )

$ <img src='https://{host_name}/web/image/blog.post/1/image_1920/hello_world.png'/>
<img src='https://helloworld.vn/hello_world.png'/>
  ```


<a name="#logger"></a>
### Logger

Đơn giản là bạn không cần khai báo biến _logger

Cách sử dụng

```
from hellpers import LOGGER


LOGGER.error()
LOGGER.info()
...
  ```

<a name="#middleware"></a>
### Middleware

Một cách tương tự như khi bạn sử dụng Dispatch.dispatch nhưng với cách nhanh gọn và clean hơn. 

<b>Lưu ý: Trong trường hợp bạn muốn enject thêm tham số khi sử lý và bên trong request không có thì cách tốt nhất 
là sử dụng <code>Dispatch.dispatch</code> để sử lý vấn đề.</b>

1. Phương thức

```middleware(auth='both')```

Trong đó: Tham số auth sẽ nhận 1 trong 3 giá trị sau: 
<code>user: Bắt buộc đăng nhập</code>
<code>none: Không bắt buộc đăng nhập. Lúc này user=1</code>
<code>both: Có thể đăng nhập hoặc không, lúc này user sẽ bằng tài khoản đưang nhập hoặc user=1 nếu không</code>

Cách sử dụng

```
from hellpers import middleware

@route(route='/hello_world', methods=['POST'], type='json')
@middleware(auth='user')
def hello_world(self):

    pass
  ```

<b>Lưu ý: @middleware chỉ sử dụng phía sau @route của odoo. Các tham số trong route nên sử dụng: methods[POST,GET,PUT,PATCH,DELETE], type='json'. Tham số auth của route là authent sử dụng cookie/session của browser, tham số auth của middleware sẽ sủ dụng cả cookie/session và access_token vậy nên trong route luôn để auth='none' nếu muốn dùng cho các môi trường khác browser</b>

<a name="#pager"></a>
### Pager

Giúp bạn đơn giản hoá việc tính toán lấy offset và limit khi phân trang dữ liệu. Và tổng hợp dữ liệu phân trang

1. Phương thức

<a name="#params"></a>
### Params

Dùng để verify dữ liệu người dùng gửi lên thông qua các rule đơn giản.

<a name="#phone_number"></a>
### PhoneNumber

Đơn giản cho việc verify số điện thoại của bạn

<a name="#query"></a>
### Query

Bạn có thể sử dụng đối tượng này để phẩn chia câu truy vấn của mình khi câu truy vấn quá phức tạp.

<b>Lưu ý: Không khuyến khích sử dụng nếu câu truy vấn đơn giản, hoặc chưa hiểu kỹ về đối tượng này.</b>

<a name="#response"></a>
### Response

Định dạng lại cấu trúc dữ liệu trả về cho client

<a name="#route"></a>
### Route

Giúp bạn thêm tiền tố, version, tên ứng dựng vào API một cách đơn giản và nhanh chóng

