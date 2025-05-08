import { Text } from "./Text";

export const Footer = () => {
  return (
    <div className="bg-black w-100vw h-[35vh] flex items-center flex-col pt-5 gap-6">
      <div className="w-min">
        <Text type="h1">
          <span className="text-white">JobPrepAI</span>
        </Text>
      </div>
      <div className="w-[40vw] opacity-75 flex justify-between">
        <Text type="h4">
          <span className="text-white">About</span>
        </Text>
        <Text type="h4">
          <span className="text-white">Our Team</span>
        </Text>
        <Text type="h4">
          <span className="text-white">Privacy Policy</span>
        </Text>
        <Text type="h4">
          <span className="text-white">Terms Of Service</span>
        </Text>
      </div>
      <div className="w-[20vw] opacity-75 flex justify-between mt-[3vh]">
        <a href="https://github.com/JakubMazurek08/CodeReactJS"><img src="/github.png" alt="GitHub" className="h-10" /></a>
        <a href="https://www.linkedin.com/in/jakub-mazurek-abb25834a/"><img src="/linkedin-logo.png" alt="LinkedIn" className="h-10" /></a>
        <a href="https://www.facebook.com/jakub.mazurek.18041"><img src="/facebook.png" alt="Facebook" className="h-10" /></a>
        
      </div>
      <div className="w-auto opacity-60 mt-[5vh]">
        <Text type="h4">
          <span className="text-white">© 2025 JobPrepAI. All rights reserved.</span>
        </Text>
      </div>
    </div>
  );
};
