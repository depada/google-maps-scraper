from bose import *
from bose.utils import merge_dicts_in_one_dict, remove_nones
import selenium


class ScrapeGoogleMapsPlacesTask(BaseTask):
    task_config = TaskConfig(output_filename="all", log_time=False, close_on_crash=True)

    browser_config = BrowserConfig(
        headless=True,
    )

    def get_data(self):
        return LocalStorage.get_item("queries", [])

    def run(self, driver, data):
        links = data["links"]
        query = data["query"]

        def get_maps_data(links):
            def get_data(link):
                def get_heading_text(max_attempts):
                    for attempt in range(1, max_attempts + 1):
                        heading = driver.get_element_or_none_by_selector(
                            "h1", Wait.SHORT
                        )

                        if heading is not None:
                            title = heading.text
                        else:
                            title = ""

                        if title == "":
                            if attempt < max_attempts:
                                print("Did Not Get Heading. Retrying ...", link)
                                driver.get(link)
                                driver.short_random_sleep()
                            else:
                                print(
                                    "Failed to retrieve heading text after 5 attempts."
                                )
                                print("Skipping...", link)
                        else:
                            return title

                    return ""

                import re

                def is_phone_num(text):
                    indian_phone_pattern = r"^(?:\+91-)?(\d{5}\s\d{5}|\d{10})"

                    if re.match(indian_phone_pattern, text):
                        return True
                    else:
                        return False

                def get_phone_numbers(max_attempts):
                    for attempt in range(1, max_attempts + 1):
                        phone_number_ele = driver.get_element_or_none(
                            "//button[starts-with(@data-item-id,'phone')]",
                            Wait.SHORT,
                        )
                        phone = (
                            phone_number_ele.get_attribute("data-item-id").replace(
                                "phone:tel:", ""
                            )
                            if phone_number_ele
                            else None
                        )
                        print("phone==>", phone)
                        if phone is not None:
                            return phone
                        else:
                            return ""
                    #     if phone_number_ele is not None:
                    #         phone_number_text = phone_number_ele.text
                    #         print(phone_number_text)
                    #     else:
                    #         phone_number_text = ""

                    #     if phone_number_text == "":
                    #         if attempt < max_attempts:
                    #             print(
                    #                 f"Did Not Get phone_number_ele (Attempt {attempt}). Retrying ...",
                    #                 link,
                    #             )
                    #             driver.get(link)
                    #             driver.short_random_sleep()
                    #         else:
                    #             print(
                    #                 "Failed to retrieve phone_number_ele text after 5 attempts."
                    #             )
                    #             print("Skipping...", link)
                    #     else:
                    #         return phone_number_text
                    # return ""

                driver.get_by_current_page_referrer(link)
                out_dict = {}
                title = get_heading_text(5)
                phone_num = get_phone_numbers(5)

                if phone_num == "":
                    return None

                if title == "":
                    return None

                out_dict["link"] = link
                out_dict["phone_num"] = phone_num
                try:
                    additional_data = driver.execute_file("get_more_data.js")
                except selenium.common.exceptions.JavascriptException as E:
                    if driver.is_in_page("consent.google.com", Wait.LONG):
                        el = driver.get_element_or_none_by_selector(
                            "form:nth-child(2) > div > div > button", Wait.LONG
                        )
                        driver.js_click(el)
                        print("Revisiting")
                        return get_data(link)
                    else:
                        print(driver.current_url)
                        driver.save_screenshot()
                        raise E

                out_dict = merge_dicts_in_one_dict(out_dict, additional_data)

                try:
                    print("Done: " + out_dict.get("title", ""))
                except:
                    pass

                return out_dict

            ls = remove_nones(list(map(get_data, links)))

            return ls

        driver.get_google()

        results = get_maps_data(links)

        return results
