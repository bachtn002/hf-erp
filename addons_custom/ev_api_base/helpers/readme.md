Mô tả các tiện ích
------------------------
####Dispatch: 
    @staticmethod 
    def dispatch(ins, action, require=[], auth=True):
        """
        Hàm kiểm tra các trường bắt bược phải có trong một dict

        @param require: 1 List các trường kiểm tra cần bắt buộc có
        @param params: 1 Dict nếu có, chứa danh sách các trường muốn được kiểm tra
        @return: Trả về True nếu mọi trường yêu cầu đều tồn có.
                 Trả về 1 ApiException nếu không tồn tại 1 trường bất kì
        """
        ...

####Authentication:
    @staticmethod
    def auth()
       """
        Hàm xác thực đăng nhập, phân quyền user

        @param require:
        @return: 
        """
        ... 

####Response:
    @staticmethod
    def Response(object)
        """
        
        @param user: 
        @param params: 
        @return: 
        """
####Route:
    Cách sử dụng: 
        Mặc định: Route(router)
        Nâng cao: Route(router, version, app)
    VD: Router('login')

####ApiException:

####Pager:

####Params:

    @staticmethod
    def verify(verify_params: list = [], data_params: dict = None):
        Hàm kiểm tra tham số theo quy tắc

        Quy tắc của tham số được sử dụng trong verify_params ví dụ như sau:

        ['user_id|int|require:partner_id',
        'partner_id|int',
        'duration|float|nullable',
        'birthday'|date:%Y-%m-%d|require',
        'start_time|datetime:%Y-%m-%d %H:%M:%S',
        'email|str:[\w\.]{3,}@[a-zA-Z]+([.a-z]{2,6}){1,4}|require',
        'user_ids|list',
        'partner_ids|tuple',
        'products|dict']

        Diễn giải:
            Tham số         |       Kiểu dữ liệu        |       Định dạng       |          Bắt buộc     |       Cho phép null       |       Ghi chú

            user_id             int                                                 yes                                                 Bắt buộc nếu có partner_id
            partner_id          int
            duration            float                                                                       yes
            birthday            date                        %Y-%m-%d                yes
            start_time          datetime                    %Y-%m-%d %H:%M:%S
            email               str                         [\w\.]{3,}@[a-...       yes
            user_ids            list
            partner_ids         tuple
            products            dict

        Các quy tắc như sau:
            * Kiểu dữ liệu: int, str, bool, list, dict, float, date, datetime
            * Bắt buộc: require
            * Cho phép null: nullable

        @param verify_params: Danh sách tham số và quy tắc áp dụng
        @param data_params: Danh sách tham số cần app dụng quy tắc
        @return: Trả về True nếu tất cả tham số được áp dụng quy tắc đều hợp lệ,
                 Trả về ApiException nếu 1 trong các tham số không đúng quy tắc
        
####LOGGER:
        
        
